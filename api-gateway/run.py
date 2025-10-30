import logging
import os
import sys
import threading
import time
from concurrent import futures
from http.server import BaseHTTPRequestHandler, HTTPServer

import grpc

sys.path.append("proto")

from gateway.seeder import run_seeder  # noqa: E402
from gateway.server import GatewayServer  # noqa: E402
from proto.gateway_pb2_grpc import add_GatewayServiceServicer_to_server  # noqa: E402


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_check_server(port=8080):
    """Runs a simple HTTP server in a background thread for health checks."""
    httpd = HTTPServer(("", port), HealthCheckHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    logging.info(f"Health check server started on port {port}")


def serve():
    """
    Initializes and starts the gRPC server and the HTTP health check server.
    """
    start_health_check_server()

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
    logging.info(f"API Gateway gRPC server started and listening on {host}")
    logging.info(f"Proxying to Glossary Service at {glossary_addr}")
    logging.info(f"Proxying to Graph Service at {graph_addr}")

    def seed_in_background():
        """
        Waits for services to be ready, then runs the seeder.
        """
        wait_seconds = 15
        logging.info(f"Seeding process will start in {wait_seconds} seconds...")
        time.sleep(wait_seconds)
        try:
            gateway_host = f"localhost:{port}"
            logging.info(f"Running seeder, connecting to gateway at {gateway_host}")
            run_seeder(gateway_host)
            logging.info("Seeding process completed successfully.")
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
