import logging
import time
from typing import Dict, Callable, Any

import grpc
from proto import (
    gateway_pb2,
    gateway_pb2_grpc,
    glossary_pb2,
    graph_pb2,
)

# The SEED_DATA dictionary remains the same.
SEED_DATA = {
    "terms": [
        {
            "name": "Microservice",
            "definition": "A software development technique that structures an application as a collection of loosely coupled services.",
        },
        {
            "name": "API Gateway",
            "definition": "An API management tool that sits between a client and a collection of backend services, acting as a reverse proxy to accept all API calls.",
        },
        {
            "name": "Containerization",
            "definition": "A form of OS virtualization where applications run in isolated user spaces called containers, sharing the same OS kernel.",
        },
        {
            "name": "Docker",
            "definition": "A platform that uses OS-level virtualization to deliver software in packages called containers.",
        },
        {
            "name": "Kubernetes",
            "definition": "An open-source container-orchestration system for automating application deployment, scaling, and management.",
        },
        {
            "name": "gRPC",
            "definition": "A high-performance, open-source universal RPC framework designed by Google.",
        },
        {
            "name": "Service Discovery",
            "definition": "The process of automatically detecting devices and services on a network, crucial for microservice architectures.",
        },
    ],
    "relationships": [
        ("API Gateway", "Microservice", "RELATED_TO"),
        ("Microservice", "API Gateway", "DEPENDS_ON"),
        ("Service Discovery", "Microservice", "RELATED_TO"),
        ("Microservice", "Service Discovery", "DEPENDS_ON"),
        ("Docker", "Containerization", "IS_A"),
        ("Kubernetes", "Containerization", "IS_A"),
        ("Kubernetes", "Docker", "RELATED_TO"),
        ("gRPC", "Microservice", "RELATED_TO"),
    ],
}


def get_relationship_type_enum(type_str: str) -> graph_pb2.RelationshipType:
    """Maps a relationship string to the corresponding protobuf enum."""
    return getattr(graph_pb2, type_str, graph_pb2.UNKNOWN)


def _call_with_retry(
    rpc_call: Callable, request: Any, max_retries: int = 5, delay_seconds: int = 3
) -> Any:
    """
    Executes a gRPC call with a retry mechanism for UNAVAILABLE errors.

    This is crucial for handling transient errors like server "cold starts"
    on serverless platforms, which manifest as 502 Bad Gateway errors
    (translating to gRPC StatusCode.UNAVAILABLE).

    Args:
        rpc_call: The gRPC stub method to call (e.g., stub.AddTerm).
        request: The protobuf request message for the call.
        max_retries: The maximum number of times to retry the call.
        delay_seconds: The time to wait between retries.

    Returns:
        The result of the successful gRPC call.

    Raises:
        grpc.RpcError: If a non-retriable error occurs or retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            return rpc_call(request)  # Execute the gRPC call
        except grpc.RpcError as e:
            # Check if the error is a transient, retriable one (like a 502)
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                logging.warning(
                    f"RPC call failed with UNAVAILABLE (likely a cold start). "
                    f"Attempt {attempt + 1}/{max_retries}. Retrying in {delay_seconds}s..."
                )
                if attempt + 1 == max_retries:
                    logging.error(
                        "Max retries reached for RPC call. Aborting operation."
                    )
                    raise  # Re-raise the last error if all retries fail
                time.sleep(delay_seconds)
            else:
                # For non-retriable errors (e.g., ALREADY_EXISTS, INVALID_ARGUMENT),
                # re-raise immediately to be handled by the main logic.
                raise e


def run_seeder(gateway_addr: str):
    """
    Connects to the gateway and seeds the database. This version makes individual
    seeding operations resilient to transient backend errors like "cold starts".
    """
    logging.info("--- Starting Database Seeder ---")
    try:
        with grpc.insecure_channel(gateway_addr) as channel:
            grpc.channel_ready_future(channel).result(timeout=10)
            logging.info("Successfully connected to the gRPC gateway.")
            stub = gateway_pb2_grpc.GatewayServiceStub(channel)
            term_map: Dict[str, str] = {}

            logging.info("--- Seeding Terms ---")
            for term_data in SEED_DATA["terms"]:
                name = term_data["name"]
                try:
                    req = glossary_pb2.AddTermRequest(
                        name=name, definition=term_data["definition"]
                    )
                    new_term = _call_with_retry(stub.AddTerm, req)
                    logging.info(f"CREATED term '{name}' with ID {new_term.id}")
                    term_map[name] = new_term.id
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                        logging.info(f"Term '{name}' already exists. Fetching ID.")
                        req = glossary_pb2.GetTermByNameRequest(name=name)
                        existing_term_res = _call_with_retry(stub.GetTermByName, req)
                        term_map[name] = existing_term_res.term.id
                    else:
                        logging.error(f"Failed to process term '{name}': {e.details()}")
                        raise

            logging.info("\n--- Seeding Relationships ---")
            for from_name, to_name, rel_type_str in SEED_DATA["relationships"]:
                from_id, to_id = term_map.get(from_name), term_map.get(to_name)
                rel_type = get_relationship_type_enum(rel_type_str)

                if not all([from_id, to_id]):
                    continue

                try:
                    req = gateway_pb2.AddRelationshipRequest(
                        from_term_id=from_id, to_term_id=to_id, type=rel_type
                    )
                    _call_with_retry(stub.AddRelationship, req)
                    logging.info(
                        f"CREATED relationship: {from_name} -[{rel_type_str}]-> {to_name}"
                    )
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                        logging.info(
                            f"Relationship {from_name} -> {to_name} already exists. Skipping."
                        )
                    else:
                        raise

            logging.info("\n--- Seeding process completed successfully! ---")

    except Exception as e:
        logging.error(
            f"A critical error occurred during the seeding process: {e}", exc_info=True
        )
