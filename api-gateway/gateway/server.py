import logging
import grpc
from itertools import chain

# Import generated classes
import sys
sys.path.append('proto')
from proto import gateway_pb2, gateway_pb2_grpc
from proto import glossary_pb2, glossary_pb2_grpc
from proto import graph_pb2, graph_pb2_grpc

class GatewayServer(gateway_pb2_grpc.GatewayServiceServicer):
    """
    Implements the gRPC API Gateway Service.
    It acts as a client to the other microservices.
    """
    def __init__(self, glossary_addr, graph_addr):
        # Create secure channels to downstream services
        self.glossary_channel = grpc.insecure_channel(glossary_addr)
        self.graph_channel = grpc.insecure_channel(graph_addr)

        # Create client stubs
        self.glossary_stub = glossary_pb2_grpc.GlossaryServiceStub(self.glossary_channel)
        self.graph_stub = graph_pb2_grpc.GraphServiceStub(self.graph_channel)
        logging.info("API Gateway initialized and connected to downstream services.")

    def GetMindMapForTerm(self, request, context):
        logging.info(f"GetMindMapForTerm request for term ID: {request.term_id}")

        try:
            # 1. Get the central term details from the Glossary Service
            central_term_req = glossary_pb2.GetTermRequest(id=request.term_id)
            central_term = self.glossary_stub.GetTerm(central_term_req)

            # 2. Get all relationships for this term from the Graph Service
            relationships_req = graph_pb2.GetRelationshipsForTermRequest(term_id=request.term_id)
            relationships_res = self.graph_stub.GetRelationshipsForTerm(relationships_req)

            # 3. Get the IDs of all neighboring terms
            neighbor_ids = set()
            for rel in relationships_res.relationships:
                neighbor_ids.add(rel.from_term_id)
                neighbor_ids.add(rel.to_term_id)
            
            # Remove the central term ID to avoid fetching it twice
            neighbor_ids.discard(request.term_id)
            
            # 4. Fetch the details for all neighboring terms from the Glossary Service
            neighbor_terms = []
            for neighbor_id in neighbor_ids:
                try:
                    term_req = glossary_pb2.GetTermRequest(id=neighbor_id)
                    term_details = self.glossary_stub.GetTerm(term_req)
                    neighbor_terms.append(term_details)
                except grpc.RpcError as e:
                     # If a neighbor isn't found, just log it and continue
                    if e.code() == grpc.StatusCode.NOT_FOUND:
                        logging.warning(f"Neighbor term with ID {neighbor_id} not found in glossary.")
                    else:
                        raise

            # 5. Assemble the final response
            all_terms = [central_term] + neighbor_terms
            nodes = [
                gateway_pb2.Node(id=t.id, name=t.name, definition=t.definition) 
                for t in all_terms
            ]
            
            # Convert enum to string label for the edge
            relationship_type_map = {v: k for k, v in graph_pb2.RelationshipType.items()}
            edges = [
                gateway_pb2.Edge(
                    from_id=r.from_term_id, 
                    to_id=r.to_term_id,
                    label=relationship_type_map.get(r.type, "UNKNOWN")
                ) for r in relationships_res.relationships
            ]

            return gateway_pb2.GetMindMapForTermResponse(nodes=nodes, edges=edges)

        except grpc.RpcError as e:
            logging.error(f"RPC failed: {e.code()} - {e.details()}")
            context.set_code(e.code())
            context.set_details(e.details())
            return gateway_pb2.GetMindMapForTermResponse()

    # --- Passthrough methods ---

    def AddTerm(self, request, context):
        """Passes the AddTerm request directly to the Glossary Service."""
        logging.info("Passing AddTerm request to Glossary Service")
        return self.glossary_stub.AddTerm(request)

    def GetTerm(self, request, context):
        """Passes the GetTerm request directly to the Glossary Service."""
        logging.info(f"Passing GetTerm request to Glossary Service for ID: {request.id}")
        return self.glossary_stub.GetTerm(request)

    def AddRelationship(self, request, context):
        """Passes the AddRelationship request directly to the Graph Service."""
        logging.info("Passing AddRelationship request to Graph Service")
        # Need to construct the correct request type for the graph service
        graph_request = graph_pb2.AddRelationshipRequest(
            from_term_id=request.from_term_id,
            to_term_id=request.to_term_id,
            type=request.type
        )
        self.graph_stub.AddRelationship(graph_request)
        return gateway_pb2.AddRelationshipResponse(message="Relationship added.")