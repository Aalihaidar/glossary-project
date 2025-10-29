"""
gRPC Servicer for the Graph Service.

Provides methods for managing the semantic relationships between glossary terms,
including creating, retrieving, and deleting these relationships.
"""

import logging
import sqlite3

import grpc
from graph.database import get_db_connection
from proto import graph_pb2, graph_pb2_grpc


class GraphServicer(graph_pb2_grpc.GraphServiceServicer):
    """
    Implements the gRPC GraphService.
    """

    def __init__(self, db_path: str):
        """
        Initializes the GraphServicer.

        Args:
            db_path: The file path to the SQLite database.
        """
        self.db_path = db_path
        logging.info(f"GraphServicer initialized with database at {db_path}")

    def AddRelationship(
        self, request: graph_pb2.AddRelationshipRequest, context
    ) -> graph_pb2.AddRelationshipResponse:
        """
        Adds a new directional relationship between two terms.

        Args:
            request: A request containing the from/to term IDs and relationship type.
            context: The gRPC request context.

        Returns:
            A response indicating the success or failure of the operation.
        """
        logging.info(
            f"AddRelationship request: {request.from_term_id} -> {request.to_term_id}"
        )

        # Input Validation
        if not all([request.from_term_id, request.to_term_id]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("The 'from' and 'to' term IDs cannot be empty.")
            return graph_pb2.AddRelationshipResponse()

        if request.from_term_id == request.to_term_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("A term cannot have a relationship with itself.")
            return graph_pb2.AddRelationshipResponse()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO relationships (from_term_id, to_term_id, type) VALUES (?, ?, ?)",
                    (request.from_term_id, request.to_term_id, request.type),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            # This assumes a UNIQUE constraint on (from_term_id, to_term_id, type)
            logging.warning("Attempted to add a duplicate relationship.")
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("This exact relationship already exists.")
            return graph_pb2.AddRelationshipResponse()
        except sqlite3.Error as e:
            logging.error(f"Database error during AddRelationship: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.AddRelationshipResponse()

        return graph_pb2.AddRelationshipResponse(success=True)

    def GetRelationshipsForTerm(
        self, request: graph_pb2.GetRelationshipsForTermRequest, context
    ) -> graph_pb2.GetRelationshipsForTermResponse:
        """
        Retrieves all relationships connected to a specific term.

        Args:
            request: A request containing the term_id to query.
            context: The gRPC request context.

        Returns:
            A response containing a list of all matching relationships.
        """
        logging.info(f"GetRelationshipsForTerm request for ID: {request.term_id}")

        if not request.term_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID cannot be empty.")
            return graph_pb2.GetRelationshipsForTermResponse()

        try:
            with get_db_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Allows accessing columns by name
                cursor = conn.cursor()
                rows = cursor.execute(
                    "SELECT * FROM relationships WHERE from_term_id = ? OR to_term_id = ?",
                    (request.term_id, request.term_id),
                ).fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error during GetRelationshipsForTerm: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.GetRelationshipsForTermResponse()

        relationships = [graph_pb2.Relationship(**row) for row in rows]
        return graph_pb2.GetRelationshipsForTermResponse(relationships=relationships)

    def DeleteRelationship(
        self, request: graph_pb2.DeleteRelationshipRequest, context
    ) -> graph_pb2.DeleteRelationshipResponse:
        """
        Deletes a specific relationship.

        Args:
            request: A request specifying the relationship to delete via its
                     from_id, to_id, and type.
            context: The gRPC request context.

        Returns:
            A response indicating the success of the deletion.
        """
        logging.info(
            f"DeleteRelationship request: {request.from_term_id} -> {request.to_term_id}"
        )

        if not all([request.from_term_id, request.to_term_id]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("The 'from' and 'to' term IDs cannot be empty.")
            return graph_pb2.DeleteRelationshipResponse()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM relationships WHERE from_term_id = ? AND to_term_id = ? AND type = ?",
                    (request.from_term_id, request.to_term_id, request.type),
                )
                conn.commit()

                if cursor.rowcount == 0:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details("The specified relationship was not found.")
                    return graph_pb2.DeleteRelationshipResponse(success=False)

        except sqlite3.Error as e:
            logging.error(f"Database error during DeleteRelationship: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return graph_pb2.DeleteRelationshipResponse(success=False)

        logging.info("Successfully deleted relationship.")
        return graph_pb2.DeleteRelationshipResponse(success=True)
