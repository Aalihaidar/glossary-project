# glossary-service/run.py

import os
import sys
import logging
from concurrent import futures
import atexit

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

sys.path.append("proto")

# --- KEY CHANGE: Import the new connection function ---
from glossary.database import init_db, create_shared_connection  # noqa: E402
from glossary.service import GlossaryServicer  # noqa: E402
from proto.glossary_pb2_grpc import add_GlossaryServiceServicer_to_server  # noqa: E402


def serve():
    """Initializes and runs the Glossary gRPC service."""
    port = os.environ.get("PORT", "50051")
    db_path = os.environ.get("DATABASE_PATH", "/tmp/glossary.db")

    # --- KEY CHANGE: Manage the DB connection lifecycle here ---
    # 1. Ensure the directory for the database exists.
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # 2. Create the single, shared connection.
    db_conn = create_shared_connection(db_path)

    # 3. Register a cleanup function to close the connection on exit.
    atexit.register(db_conn.close)

    # 4. Initialize the database schema using the shared connection.
    init_db(db_conn)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 5. Inject the shared connection into the servicer.
    add_GlossaryServiceServicer_to_server(GlossaryServicer(db_conn), server)

    # Add the standard gRPC Health Servicer
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set(
        "glossary.GlossaryService", health_pb2.HealthCheckResponse.SERVING
    )
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"Glossary Service gRPC server started and listening on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    serve()
