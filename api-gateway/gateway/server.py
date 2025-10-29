"""
gRPC Servicer for the API Gateway.

Acts as the single entry point for the system, proxying requests to the
appropriate downstream microservices (Glossary and Graph services) and
orchestrating complex queries like GetMindMapForTerm.
"""

import logging
import grpc

from proto import (
    gateway_pb2,
    gateway_pb2_grpc,
    glossary_pb2,
    glossary_pb2_grpc,
    graph_pb2,  # <-- THIS IS THE MISSING IMPORT
    graph_pb2_grpc,
)


def handle_rpc_error(e: grpc.RpcError, context):
    """A helper function to propagate gRPC errors from downstream services."""
    logging.error(f"Downstream RPC failed: {e.code()} - {e.details()}")
    context.set_code(e.code())
    context.set_details(e.details())


class GatewayServer(gateway_pb2_grpc.GatewayServiceServicer):
    """
    Implements the gRPC GatewayService, proxying requests and handling orchestration.
    """

    def __init__(self, glossary_addr: str, graph_addr: str):
        self.glossary_channel = grpc.insecure_channel(glossary_addr)
        self.graph_channel = grpc.insecure_channel(graph_addr)
        self.glossary_stub = glossary_pb2_grpc.GlossaryServiceStub(
            self.glossary_channel
        )
        self.graph_stub = graph_pb2_grpc.GraphServiceStub(self.graph_channel)
        logging.info("API Gateway initialized and connected to downstream services.")

    # --- Glossary Service Proxy Methods ---

    def AddTerm(self, request, context):
        logging.info("Proxying AddTerm request to Glossary Service")
        try:
            return self.glossary_stub.AddTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.Term()

    def GetTerm(self, request, context):
        logging.info(f"Proxying GetTerm for ID: {request.id}")
        try:
            return self.glossary_stub.GetTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.Term()

    def GetAllTerms(self, request, context):
        logging.info("Proxying GetAllTerms request to Glossary Service")
        try:
            return self.glossary_stub.GetAllTerms(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.GetAllTermsResponse()

    def UpdateTerm(self, request, context):
        logging.info(f"Proxying UpdateTerm for ID: {request.id}")
        try:
            return self.glossary_stub.UpdateTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.Term()

    def DeleteTerm(self, request, context):
        logging.info(f"Proxying DeleteTerm for ID: {request.id}")
        try:
            return self.glossary_stub.DeleteTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return glossary_pb2.DeleteTermResponse()

    # --- Graph Service Proxy Methods ---

    def AddRelationship(self, request, context):
        logging.info("Proxying AddRelationship request to Graph Service")
        try:
            # We must use the imported graph_pb2 to create the request object
            graph_request = graph_pb2.AddRelationshipRequest(
                from_term_id=request.from_term_id,
                to_term_id=request.to_term_id,
                type=request.type,
            )
            return self.graph_stub.AddRelationship(graph_request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.AddRelationshipResponse()

    def GetRelationshipsForTerm(self, request, context):
        logging.info(f"Proxying GetRelationshipsForTerm for ID: {request.term_id}")
        try:
            return self.graph_stub.GetRelationshipsForTerm(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return graph_pb2.GetRelationshipsForTermResponse()

    def DeleteRelationship(self, request, context):
        logging.info("Proxying DeleteRelationship request to Graph Service")
        try:
            return self.graph_stub.DeleteRelationship(request)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return graph_pb2.DeleteRelationshipResponse()

    # --- Composite/Orchestration Methods ---

    def GetMindMapForTerm(self, request, context):
        logging.info(f"Orchestrating GetMindMapForTerm for ID: {request.term_id}")
        try:
            # 1. Get the central term from the glossary service
            central_term = self.glossary_stub.GetTerm(
                glossary_pb2.GetTermRequest(id=request.term_id)
            )

            # 2. Get all relationships for that term from the graph service
            relationships_res = self.graph_stub.GetRelationshipsForTerm(
                graph_pb2.GetRelationshipsForTermRequest(term_id=request.term_id)
            )

            # 3. Gather all unique neighbor term IDs
            neighbor_ids = set()
            for rel in relationships_res.relationships:
                neighbor_ids.add(rel.from_term_id)
                neighbor_ids.add(rel.to_term_id)
            neighbor_ids.discard(request.term_id)

            # 4. Fetch the details for each neighbor term from the glossary service
            neighbor_terms = []
            for neighbor_id in neighbor_ids:
                term_details = self.glossary_stub.GetTerm(
                    glossary_pb2.GetTermRequest(id=neighbor_id)
                )
                neighbor_terms.append(term_details)

            # 5. Assemble the final response
            all_terms = [central_term] + neighbor_terms
            nodes = [
                gateway_pb2.Node(id=t.id, name=t.name, definition=t.definition)
                for t in all_terms
            ]

            relationship_type_map = {
                v: k for k, v in graph_pb2.RelationshipType.items()
            }
            edges = [
                gateway_pb2.Edge(
                    from_id=r.from_term_id,
                    to_id=r.to_term_id,
                    label=relationship_type_map.get(r.type, "UNKNOWN"),
                )
                for r in relationships_res.relationships
            ]

            return gateway_pb2.GetMindMapForTermResponse(nodes=nodes, edges=edges)

        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.GetMindMapForTermResponse()
