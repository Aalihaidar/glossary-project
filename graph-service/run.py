import os
import sys
import logging
import threading
from concurrent import futures
from http.server import BaseHTTPRequestHandler, HTTPServer

import grpc

# Add the generated proto files to the Python path
sys.path.append("proto")

from graph.database import init_db  # noqa: E402
from graph.service import GraphServicer  # noqa: E402
from proto.graph_pb2_grpc import add_GraphServiceServicer_to_server  # noqa: E402


class HealthCheckHandler(BaseHTTPRequestHandler):
    """A simple HTTP handler for Render's health checks."""

    def do_GET(self):
        """Responds with a 200 OK for the /healthz path."""
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppresses the default logging for quiet health check pings."""
        return


def start_health_check_server(port):
    """
    Runs a simple HTTP server in a separate thread.
    This is required for platforms like Render that expect a web service
    to bind to a specific port for health monitoring.
    """
    httpd = HTTPServer(("", port), HealthCheckHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True  # Allows main thread to exit even if this thread is running
    thread.start()
    logging.info(f"Health check server started on port {port}")


def serve():
    """
    Initializes and runs the Graph gRPC service.
    This function also starts a separate HTTP health check server to comply
    with the hosting platform's requirements.
    """
    # --- Health Check Server Initialization ---
    # Render provides a PORT environment variable that it expects the service
    # to listen on for health checks. We read it here.
    health_check_port = int(os.environ.get("PORT", 8080))
    start_health_check_server(health_check_port)

    # --- gRPC Server Initialization ---
    # The gRPC server runs on a dedicated internal port, ignoring the PORT
    # variable used by the health checker.
    grpc_port = "50052"
    db_path = os.environ.get("DATABASE_PATH", "/tmp/graph.db")

    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GraphServiceServicer_to_server(GraphServicer(db_path), server)

    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    logging.info(f"Graph Service gRPC server started on internal port {grpc_port}")

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
