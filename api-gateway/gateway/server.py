"""
gRPC Servicer for the API Gateway.

This service is the single public-facing entry point for the entire system.
It acts as a proxy for simple CRUD operations and as an orchestrator for
complex queries that require data from multiple downstream microservices.
"""

import logging
import time
from typing import Dict, Set

import grpc
from proto import (
    gateway_pb2,
    gateway_pb2_grpc,
    glossary_pb2,
    glossary_pb2_grpc,
    graph_pb2,
    graph_pb2_grpc,
)


def handle_rpc_error(e: grpc.RpcError, context):
    """A centralized helper function to propagate gRPC errors from downstream services."""
    logging.error(f"Downstream RPC failed: {e.code()} - {e.details()}")
    context.set_code(e.code())
    context.set_details(e.details())
    return None


def wait_for_channel_ready(address: str, service_name: str) -> grpc.Channel:
    """
    Waits for a gRPC channel to be ready, retrying if necessary.
    This version creates a SECURE channel, suitable for communicating with
    public-facing services that have TLS enabled.
    """
    logging.info(f"Attempting to connect to {service_name} at {address}...")
    max_retries = 12
    retry_delay_seconds = 10
    attempt = 0

    while attempt < max_retries:
        try:
            attempt += 1
            # --- THE FINAL KEY CHANGE ---
            # Use grpc.secure_channel because we are connecting to a public
            # Render URL, which has TLS encryption managed automatically.
            # grpc.ssl_channel_credentials() uses the system's default CA certs.
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(address, credentials)

            grpc.channel_ready_future(channel).result(timeout=5)
            logging.info(f"Successfully connected to {service_name}.")
            return channel
        except grpc.FutureTimeoutError:
            logging.warning(
                f"Connection to {service_name} timed out on attempt {attempt}/{max_retries}. "
                f"Retrying in {retry_delay_seconds} seconds..."
            )
            if channel:
                channel.close()
            time.sleep(retry_delay_seconds)

    raise RuntimeError(
        f"Could not connect to {service_name} at {address} after {max_retries} attempts."
    )


class GatewayServer(gateway_pb2_grpc.GatewayServiceServicer):
    """
    Implements the gRPC GatewayService, handling all proxying and orchestration logic.
    """

    def __init__(self, glossary_addr: str, graph_addr: str):
        """
        Initializes the GatewayServer and establishes RESILIENT connections to
        downstream services, waiting for them to be ready.
        """
        self.glossary_channel = wait_for_channel_ready(
            glossary_addr, "Glossary Service"
        )
        self.graph_channel = wait_for_channel_ready(graph_addr, "Graph Service")

        self.glossary_stub = glossary_pb2_grpc.GlossaryServiceStub(
            self.glossary_channel
        )
        self.graph_stub = graph_pb2_grpc.GraphServiceStub(self.graph_channel)
        logging.info("API Gateway initialized. All downstream services are connected.")

    # ... The rest of the class methods remain unchanged ...

    def _get_term_lookup(self, term_ids: Set[str]) -> Dict[str, glossary_pb2.Term]:
        """
        Fetches term data for a set of IDs and returns a lookup map.

        NOTE: This implementation uses a loop of individual GetTerm calls, which can
        lead to performance issues (the N+1 query problem). A professional-grade
        optimization would be to add a `GetTermsByIds` batch RPC to the Glossary service.

        Args:
            term_ids: A set of term IDs to fetch.

        Returns:
            A dictionary mapping term IDs to Term objects.
        """
        term_lookup = {}
        for term_id in term_ids:
            try:
                term = self.glossary_stub.GetTerm(
                    glossary_pb2.GetTermRequest(id=term_id)
                )
                term_lookup[term_id] = term
            except grpc.RpcError as e:
                logging.warning(
                    f"Could not fetch details for term ID {term_id}: {e.details()}"
                )
        return term_lookup

    def _get_term_details(self, term: glossary_pb2.Term) -> gateway_pb2.TermDetails:
        """
        Helper function to enrich a Term object with detailed relationships.

        This is a core orchestration component. It fetches relationship IDs from
        the graph service, then fetches the names for those IDs from the glossary
        service, and finally assembles an enriched response.

        Args:
            term: A Term object from the glossary service.

        Returns:
            An enriched TermDetails object containing the term and its detailed relationships.
        """
        try:
            relationships_res = self.graph_stub.GetRelationshipsForTerm(
                graph_pb2.GetRelationshipsForTermRequest(term_id=term.id)
            )
            if not relationships_res.relationships:
                return gateway_pb2.TermDetails(term=term)

            related_ids = set()
            for rel in relationships_res.relationships:
                related_ids.add(rel.from_term_id)
                related_ids.add(rel.to_term_id)

            term_lookup = self._get_term_lookup(related_ids)
            if term.id not in term_lookup:
                term_lookup[term.id] = term

            enriched_relationships = []
            for rel in relationships_res.relationships:
                from_term = term_lookup.get(rel.from_term_id)
                to_term = term_lookup.get(rel.to_term_id)

                if from_term and to_term:
                    enriched_relationships.append(
                        gateway_pb2.RelationshipDetails(
                            from_term_id=rel.from_term_id,
                            to_term_id=rel.to_term_id,
                            type=rel.type,
                            from_term_name=from_term.name,
                            to_term_name=to_term.name,
                        )
                    )
            return gateway_pb2.TermDetails(
                term=term, relationships=enriched_relationships
            )
        except grpc.RpcError:
            logging.warning(
                f"Could not fetch relationships for term ID {term.id}. "
                "Returning term data only."
            )
            return gateway_pb2.TermDetails(term=term)

    def GetTerm(
        self, request: glossary_pb2.GetTermRequest, context
    ) -> gateway_pb2.TermDetails:
        """Orchestrates retrieving a single term and enriching it with its relationships."""
        logging.info(f"Orchestrating GetTerm for ID: {request.id}")
        try:
            term = self.glossary_stub.GetTerm(request)
            return self._get_term_details(term)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.TermDetails()

    def GetTermByName(
        self, request: glossary_pb2.GetTermByNameRequest, context
    ) -> gateway_pb2.TermDetails:
        """Orchestrates retrieving a single term by name and enriching it."""
        logging.info(f"Orchestrating GetTermByName for name: {request.name}")
        try:
            term = self.glossary_stub.GetTermByName(request)
            return self._get_term_details(term)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.TermDetails()

    def SearchTerms(
        self, request: glossary_pb2.SearchTermsRequest, context
    ) -> gateway_pb2.SearchTermsResponse:
        """Orchestrates searching for terms and enriching each result."""
        logging.info(f"Orchestrating SearchTerms for query: '{request.query}'")
        try:
            search_results = self.glossary_stub.SearchTerms(request)
            rich_results = [
                self._get_term_details(term) for term in search_results.terms
            ]
            return gateway_pb2.SearchTermsResponse(results=rich_results)
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.SearchTermsResponse()

    def GetMindMapForTerm(
        self, request: gateway_pb2.GetMindMapForTermRequest, context
    ) -> gateway_pb2.GetMindMapForTermResponse:
        """Orchestrates fetching all data needed to render a visual mind map."""
        logging.info(f"Orchestrating GetMindMapForTerm for ID: {request.term_id}")
        try:
            relationships_res = self.graph_stub.GetRelationshipsForTerm(
                graph_pb2.GetRelationshipsForTermRequest(term_id=request.term_id)
            )

            all_term_ids = {request.term_id}
            for rel in relationships_res.relationships:
                all_term_ids.add(rel.from_term_id)
                all_term_ids.add(rel.to_term_id)

            term_lookup = self._get_term_lookup(all_term_ids)

            nodes = [
                gateway_pb2.Node(id=t.id, name=t.name, definition=t.definition)
                for t in term_lookup.values()
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

    def AddTerm(self, request, context):
        logging.info("Proxying AddTerm request to Glossary Service")
        try:
            return self.glossary_stub.AddTerm(request)
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

    def AddRelationship(self, request, context):
        logging.info("Proxying AddRelationship request to Graph Service")
        try:
            graph_response = self.graph_stub.AddRelationship(request)
            return gateway_pb2.AddRelationshipResponse(success=graph_response.success)
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
            graph_response = self.graph_stub.DeleteRelationship(request)
            return gateway_pb2.DeleteRelationshipResponse(
                success=graph_response.success
            )
        except grpc.RpcError as e:
            handle_rpc_error(e, context)
            return gateway_pb2.DeleteRelationshipResponse()
