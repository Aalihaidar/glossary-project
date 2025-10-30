# graph-service/graph/service.py

"""
gRPC Servicer for the Graph Service.

Provides methods for managing relationships between glossary terms using a single,
shared SQLite connection, which is the recommended pattern for server applications.
"""

import logging
import sqlite3

import grpc
from proto import graph_pb2, graph_pb2_grpc


class GraphServicer(graph_pb2_grpc.GraphServiceServicer):
    """
    Implements the gRPC GraphService.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initializes the GraphServicer with a shared database connection.

        Args:
            conn: A shared, thread-safe sqlite3.Connection object.
        """
        self.conn = conn
        logging.info("GraphServicer initialized with a shared database connection.")

    def AddRelationship(
        self, request: graph_pb2.AddRelationshipRequest, context
    ) -> graph_pb2.AddRelationshipResponse:
        """Adds a new directional relationship between two terms."""
        logging.info(
            f"AddRelationship request: {request.from_term_id} -> {request.to_term_id}"
        )
        if not all([request.from_term_id, request.to_term_id]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("The 'from' and 'to' term IDs cannot be empty.")
            return graph_pb2.AddRelationshipResponse()
        if request.from_term_id == request.to_term_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("A term cannot have a relationship with itself.")
            return graph_pb2.AddRelationshipResponse()

        try:
            # Use the shared connection directly
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO relationships (from_term_id, to_term_id, type) VALUES (?, ?, ?)",
                (request.from_term_id, request.to_term_id, request.type),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("This exact relationship already exists.")
            return graph_pb2.AddRelationshipResponse()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.AddRelationshipResponse()

        return graph_pb2.AddRelationshipResponse(success=True)

    def GetRelationshipsForTerm(
        self, request: graph_pb2.GetRelationshipsForTermRequest, context
    ) -> graph_pb2.GetRelationshipsForTermResponse:
        """Retrieves all relationships connected to a specific term."""
        if not request.term_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID cannot be empty.")
            return graph_pb2.GetRelationshipsForTermResponse()

        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            rows = cursor.execute(
                "SELECT * FROM relationships WHERE from_term_id = ? OR to_term_id = ?",
                (request.term_id, request.term_id),
            ).fetchall()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.GetRelationshipsForTermResponse()

        relationships = [graph_pb2.Relationship(**row) for row in rows]
        return graph_pb2.GetRelationshipsForTermResponse(relationships=relationships)

    def DeleteRelationship(
        self, request: graph_pb2.DeleteRelationshipRequest, context
    ) -> graph_pb2.DeleteRelationshipResponse:
        """Deletes a specific relationship."""
        if not all([request.from_term_id, request.to_term_id]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("The 'from' and 'to' term IDs cannot be empty.")
            return graph_pb2.DeleteRelationshipResponse()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM relationships WHERE from_term_id = ? AND to_term_id = ? AND type = ?",
                (request.from_term_id, request.to_term_id, request.type),
            )
            self.conn.commit()
            if cursor.rowcount == 0:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("The specified relationship was not found.")
                return graph_pb2.DeleteRelationshipResponse(success=False)
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.DeleteRelationshipResponse(success=False)

        return graph_pb2.DeleteRelationshipResponse(success=True)
