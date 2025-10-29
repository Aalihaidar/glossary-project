import os
import logging
from concurrent import futures
import grpc
from gateway.server import GatewayServer

# Import generated classes
import sys
sys.path.append('proto')
from proto.gateway_pb2_grpc import add_GatewayServiceServicer_to_server

def serve():
    """Starts the gRPC server."""
    port = os.environ.get('PORT', '50050')
    glossary_addr = os.environ.get('GLOSSARY_SERVICE_ADDR', 'localhost:50051')
    graph_addr = os.environ.get('GRAPH_SERVICE_ADDR', 'localhost:50052')

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GatewayServiceServicer_to_server(GatewayServer(glossary_addr, graph_addr), server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logging.info(f"API Gateway started on port {port}")
    logging.info(f"Proxying to Glossary Service at {glossary_addr}")
    logging.info(f"Proxying to Graph Service at {graph_addr}")
    
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()