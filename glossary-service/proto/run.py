import os
import logging
from concurrent import futures
import grpc
from glossary.service import GlossaryServicer
from glossary.database import init_db

# Import generated classes
import sys

sys.path.append("proto")
from proto.glossary_pb2_grpc import add_GlossaryServiceServicer_to_server


def serve():
    """Starts the gRPC server."""
    port = os.environ.get("PORT", "50051")
    db_path = os.environ.get("DATABASE_PATH", "data/glossary.db")

    # Initialize the database
    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GlossaryServiceServicer_to_server(GlossaryServicer(db_path), server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"Glossary Service started on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
