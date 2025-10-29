"""
gRPC Servicer for the API Gateway.

Acts as the single entry point for the system, proxying requests to the
appropriate downstream microservices (Glossary and Graph services).
"""

import logging
import grpc

from proto import (
    gateway_pb2_grpc,
    glossary_pb2_grpc,
    graph_pb2_grpc,
)

# It's good practice to handle potential RpcError for clean error propagation
def handle_rpc_error(e, context):
    """A helper function to propagate gRPC errors from downstream services."""
    logging.error(f"Downstream RPC failed: {e.code()} - {e.details()}")
    context.set_code(e.code())
    context.set_details(e.details())

class GatewayServer(gateway_pb2_grpc.GatewayServiceServicer):
    """
    Implements the gRPC GatewayService, proxying requests to downstream services.
    """
    def __init__(self, glossary_addr: str, graph_addr: str):
        self.glossary_channel = grpc.insecure_channel(glossary_addr)
        self.graph_channel = grpc.insecure_channel(graph_addr)

        self.glossary_stub = glossary_pb2_grpc.GlossaryServiceStub(self.glossary_channel)
        self.graph_stub = graph_pb2_grpc.GraphServiceStub(self.graph_channel)
        logging.info("API Gateway initialized and connected to downstream services.")

    # --- Glossary Service Proxy Methods ---

    def AddTerm(self, request, context):
        """Passes the AddTerm request directly to the Glossary Service."""
        logging.info("Proxying AddTerm request to Glossary Service")
        try:
            return self.glossary_stub.AddTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            # Return an empty object of the correct type on error
            return glossary_pb2.Term()

    def GetTerm(self, request, context):
        """Passes the GetTerm request directly to the Glossary Service."""
        logging.info(f"Proxying GetTerm for ID: {request.id}")
        try:
            return self.glossary_stub.GetTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.Term()

    def GetAllTerms(self, request, context):
        """Passes the GetAllTerms request directly to the Glossary Service."""
        logging.info("Proxying GetAllTerms request to Glossary Service")
        try:
            return self.glossary_stub.GetAllTerms(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.GetAllTermsResponse()

    def UpdateTerm(self, request, context):
        """Passes the UpdateTerm request directly to the Glossary Service."""
        logging.info(f"Proxying UpdateTerm for ID: {request.id}")
        try:
            return self.glossary_stub.UpdateTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.Term()

    def DeleteTerm(self, request, context):
        """Passes the DeleteTerm request directly to the Glossary Service."""
        logging.info(f"Proxying DeleteTerm for ID: {request.id}")
        try:
            return self.glossary_stub.DeleteTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.DeleteTermResponse()

    # --- Graph Service Proxy Methods ---

    def AddRelationship(self, request, context):
        """Passes the AddRelationship request to the Graph Service."""
        logging.info("Proxying AddRelationship request to Graph Service")
        try:
            # We must convert the gateway request to the graph service request
            graph_request = graph_pb2.AddRelationshipRequest(
                from_term_id=request.from_term_id,
                to_term_id=request.to_term_id,
                type=request.type,
            )
            return self.graph_stub.AddRelationship(graph_request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return graph_pb2.AddRelationshipResponse()
    
    # You can add the GetMindMapForTerm method here as well, refactored for clarity if you wish.
    # The original implementation was complex and is omitted here for focus, but it should be added back.