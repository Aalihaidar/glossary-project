import logging
import time
from typing import Dict

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


def run_seeder(gateway_addr: str):
    """
    Connects to the gateway and seeds the database.
    This function includes a robust retry mechanism to handle startup race
    conditions where downstream services may not be immediately available.
    """
    logging.info("--- Starting Database Seeder ---")

    # --- KEY CHANGE: Retry Logic ---
    # We will try to connect multiple times to give the gateway and its
    # downstream services time to come online.
    max_retries = 12
    retry_delay_seconds = 10
    attempt = 0

    while attempt < max_retries:
        try:
            attempt += 1
            logging.info(
                f"Attempting to connect to gateway at {gateway_addr} "
                f"(Attempt {attempt}/{max_retries})..."
            )

            # Establish the channel within the loop
            with grpc.insecure_channel(gateway_addr) as channel:
                # Wait for the channel to be ready, with a short timeout.
                # If this fails, it will raise an exception and trigger the retry.
                grpc.channel_ready_future(channel).result(timeout=5)
                logging.info("Successfully connected to the gRPC service.")

                stub = gateway_pb2_grpc.GatewayServiceStub(channel)
                term_map: Dict[str, str] = {}  # Cache for term name -> term ID

                logging.info("--- Seeding Terms ---")
                for term_data in SEED_DATA["terms"]:
                    name = term_data["name"]
                    try:
                        req = glossary_pb2.AddTermRequest(
                            name=name, definition=term_data["definition"]
                        )
                        new_term = stub.AddTerm(req)
                        logging.info(f"CREATED term '{name}' with ID {new_term.id}")
                        term_map[name] = new_term.id
                    except grpc.RpcError as e:
                        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                            logging.info(f"Term '{name}' already exists. Fetching ID.")
                            req = glossary_pb2.GetTermByNameRequest(name=name)
                            existing_term = stub.GetTermByName(req)
                            term_map[name] = existing_term.term.id
                        else:
                            # Re-raise other gRPC errors to be caught by the outer loop
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
                        stub.AddRelationship(req)
                        logging.info(
                            f"CREATED relationship: {from_name} -[{rel_type_str}]-> {to_name}"
                        )
                    except grpc.RpcError as e:
                        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                            logging.info(
                                f"Relationship {from_name} -> {to_name} already exists. Skipping."
                            )
                        else:
                            # Re-raise other gRPC errors
                            raise

                logging.info("\n--- Seeding process completed successfully! ---")
                return  # Exit the function successfully

        except (grpc.FutureTimeoutError, grpc.RpcError) as e:
            # This block catches connection failures (UNAVAILABLE) or timeouts.
            code = e.code() if isinstance(e, grpc.RpcError) else "Timeout"
            logging.warning(
                f"Seeder connection failed (Code: {code}). "
                f"Gateway or downstream service may not be ready."
            )
            if attempt < max_retries:
                logging.info(f"Retrying in {retry_delay_seconds} seconds...")
                time.sleep(retry_delay_seconds)
            else:
                logging.error(
                    "Seeding failed after multiple retries. Aborting.", exc_info=True
                )
                # Exit with an error status if you want to fail the deployment
                # For this tutorial, we will let it continue.

    logging.error(
        "--- Seeding failed. The seeder was unable to connect to the gateway. ---"
    )
