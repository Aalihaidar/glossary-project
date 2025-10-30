import os
import logging
from concurrent import futures
import grpc
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append("proto")

from graph.service import GraphServicer  # noqa: E402
from graph.database import init_db  # noqa: E402
from proto.graph_pb2_grpc import add_GraphServiceServicer_to_server  # noqa: E402


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
    with HTTPServer(("", port), HealthCheckHandler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True
        thread.start()
        logging.info(f"Health check server started on port {port}")


def serve():
    """Starts the gRPC server and health check server."""
    start_health_check_server()

    port = os.environ.get("PORT", "50052")
    db_path = os.environ.get("DATABASE_PATH", "data/graph.db")

    init_db(db_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GraphServiceServicer_to_server(GraphServicer(db_path), server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info(f"Graph Service started on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    serve()
