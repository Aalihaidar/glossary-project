# graph-service/run.py

import os
import sys
import logging
from concurrent import futures

import grpc

# --- KEY CHANGE: Import gRPC Health Checking Libraries ---
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

# Add the generated proto files to the Python path
sys.path.append("proto")

from graph.database import init_db  # noqa: E402
from graph.service import GraphServicer  # noqa: E402
from proto.graph_pb2_grpc import add_GraphServiceServicer_to_server  # noqa: E402


def serve():
    """
    Initializes and runs the Graph gRPC service.

    This version binds the gRPC server directly to the port specified by the
    PORT environment variable, making it compatible with cloud platforms like Render.
    It also implements the standard gRPC Health Checking Protocol, which Render
    uses to verify that the service is running correctly.
    """
    # --- KEY CHANGE: Use PORT for the main gRPC server ---
    # We no longer run on a custom internal port. We bind directly to the
    # port Render's load balancer will forward traffic to.
    # Default to 50052 for easy local development.
    port = os.environ.get("PORT", "50052")
    db_path = os.environ.get("DATABASE_PATH", "/tmp/graph.db")

    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add our main Graph service servicer
    add_GraphServiceServicer_to_server(GraphServicer(db_path), server)

    # --- KEY CHANGE: Add the standard gRPC Health Servicer ---
    # The HTTP health server is removed. This is the new, standard way.
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Set the health status for our service.
    # The empty string "" denotes the overall health of the server.
    # We also explicitly set the status for our specific service.
    service_name = "graph.GraphService"
    health_servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"Graph Service gRPC server started and listening on port {port}")

    # The main thread will block here, keeping the gRPC server running.
    server.wait_for_termination()


if __name__ == "__main__":
    # Configure professional logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    serve()
