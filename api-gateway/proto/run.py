import logging
import os
import sys
import threading
import time
from concurrent import futures

import grpc

sys.path.append("proto")

from gateway.seeder import run_seeder  # noqa: E402
from gateway.server import GatewayServer  # noqa: E402
from proto.gateway_pb2_grpc import add_GatewayServiceServicer_to_server  # noqa: E402


def serve():
    """
    Initializes and starts the gRPC server for the API Gateway,
    and orchestrates the database seeding process on startup for
    ephemeral environments like Render.
    """
    port = os.environ.get("PORT", "50050")
    glossary_addr = os.environ.get("GLOSSARY_SERVICE_ADDR", "localhost:50051")
    graph_addr = os.environ.get("GRAPH_SERVICE_ADDR", "localhost:50052")
    host = f"[::]:{port}"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GatewayServiceServicer_to_server(
        GatewayServer(glossary_addr, graph_addr), server
    )
    server.add_insecure_port(host)
    server.start()
    logging.info(f"API Gateway server started and listening on {host}")
    logging.info(f"Proxying to Glossary Service at {glossary_addr}")
    logging.info(f"Proxying to Graph Service at {graph_addr}")

    def seed_in_background():
        logging.info("Seeder will start in 2 seconds...")
        time.sleep(2)
        try:
            run_seeder(f"localhost:{port}")
        except Exception as e:
            logging.error(f"Seeding process failed: {e}", exc_info=True)

    seeder_thread = threading.Thread(target=seed_in_background)
    seeder_thread.daemon = True
    seeder_thread.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutting down the server due to KeyboardInterrupt.")
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    serve()
