import logging
from typing import Dict

import grpc
from proto import (  # Corrected imports
    gateway_pb2,
    gateway_pb2_grpc,
    glossary_pb2,  # Added direct import for glossary messages
    graph_pb2,
)

# Rich Professional Data Set
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


def wait_for_service(channel, timeout=10):
    """Waits for the gRPC service to be ready."""
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout)
        logging.info("Successfully connected to the gRPC service.")
    except grpc.FutureTimeoutError:
        logging.error(f"Connection to service timed out after {timeout} seconds.")
        raise


def run_seeder(gateway_addr: str):
    """
    Connects to the gateway and seeds the database with terms and relationships.
    This function is idempotent and safe to run on every startup.
    """
    logging.info("--- Starting Database Seeder ---")
    try:
        with grpc.insecure_channel(gateway_addr) as channel:
            wait_for_service(channel)
            stub = gateway_pb2_grpc.GatewayServiceStub(channel)
            term_map: Dict[str, str] = {}  # Cache for term name -> term ID

            logging.info("--- Seeding Terms ---")
            for term_data in SEED_DATA["terms"]:
                name = term_data["name"]
                try:
                    # CORRECTED: Use glossary_pb2 directly
                    req = glossary_pb2.AddTermRequest(
                        name=name, definition=term_data["definition"]
                    )
                    new_term = stub.AddTerm(req)
                    logging.info(f"CREATED term '{name}' with ID {new_term.id}")
                    term_map[name] = new_term.id
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                        logging.info(f"Term '{name}' already exists. Fetching ID.")
                        # CORRECTED: Use glossary_pb2 directly
                        req = glossary_pb2.GetTermByNameRequest(name=name)
                        existing_term = stub.GetTermByName(req)
                        term_map[name] = existing_term.term.id
                    else:
                        logging.error(f"Failed to process term '{name}': {e.details()}")
                        raise

            logging.info("\n--- Seeding Relationships ---")
            for from_name, to_name, rel_type_str in SEED_DATA["relationships"]:
                from_id = term_map.get(from_name)
                to_id = term_map.get(to_name)
                rel_type = get_relationship_type_enum(rel_type_str)

                if not all([from_id, to_id]):
                    logging.warning(
                        f"Skipping relationship due to missing term: {from_name} -> {to_name}"
                    )
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
                        logging.error(
                            f"Failed to create relationship {from_name} -> {to_name}: {e.details()}"
                        )

            logging.info("\n--- Seeding complete! ---")

    except Exception as e:
        logging.error(
            f"An error occurred during the seeding process: {e}", exc_info=True
        )
