import os
import logging
from concurrent import futures
import grpc

# Add the proto path to the system path first
import sys

sys.path.append("proto")

from graph.service import GraphServicer  # noqa: E402
from graph.database import init_db  # noqa: E402
from proto.graph_pb2_grpc import add_GraphServiceServicer_to_server  # noqa: E402


def serve():
    """Starts the gRPC server."""
    port = os.environ.get("PORT", "50052")
    db_path = os.environ.get("DATABASE_PATH", "data/graph.db")

    # Initialize the database
    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GraphServiceServicer_to_server(GraphServicer(db_path), server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"Graph Service started on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
