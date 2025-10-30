import os
import logging
from concurrent import futures
import grpc
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append("proto")

from glossary.service import GlossaryServicer  # noqa: E402
from glossary.database import init_db  # noqa: E402
from proto.glossary_pb2_grpc import add_GlossaryServiceServicer_to_server  # noqa: E402


# --- Health Check Handler (Stays the same) ---
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
        # Suppress logging for health checks
        return


def start_health_check_server(port=8080):
    """Runs a simple HTTP server in a background thread for health checks."""
    # This server must keep running for Render's health checks to pass.
    # It does not use a 'with' statement.
    httpd = HTTPServer(("", port), HealthCheckHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    logging.info(f"Health check server started on port {port}")


# --- End Health Check ---


def serve():
    """Starts the gRPC server on a dedicated internal port and the health check server."""
    # Start the mandatory health check server in the background.
    start_health_check_server()

    # --- KEY CHANGE ---
    # We IGNORE the 'PORT' env var from Render for our gRPC server.
    # We use a dedicated internal port for service-to-service communication.
    grpc_port = "50051"
    db_path = os.environ.get("DATABASE_PATH", "/tmp/glossary.db")

    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GlossaryServiceServicer_to_server(GlossaryServicer(db_path), server)

    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    logging.info(f"Glossary Service gRPC server started on internal port {grpc_port}")

    # Keep the main thread alive for the gRPC server
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    serve()
