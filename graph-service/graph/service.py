import logging
import grpc

# Import generated classes
import sys
sys.path.append('proto')
from proto import graph_pb2
from proto import graph_pb2_grpc

from graph.database import get_db_connection

class GraphServicer(graph_pb2_grpc.GraphServiceServicer):
    """Implements the gRPC Graph Service."""

    def __init__(self, db_path):
        self.db_path = db_path

    def AddRelationship(self, request, context):
        logging.info(f"AddRelationship request received: {request.from_term_id} -> {request.to_term_id}")
        conn = get_db_connection(self.db_path)
        
        try:
            # Insert the forward relationship
            conn.execute(
                "INSERT INTO relationships (from_term_id, to_term_id, type) VALUES (?, ?, ?)",
                (request.from_term_id, request.to_term_id, request.type)
            )
            # To make lookups easier, we can insert the reverse relationship for non-directional queries
            # For simplicity here, we assume directed relationships.
            conn.commit()
        except conn.IntegrityError:
            # This handles cases where the relationship already exists
            msg = "Relationship already exists."
            logging.warning(msg)
            # Not an error, so we don't set context code
            return graph_pb2.AddRelationshipResponse(message=msg)
        except conn.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return graph_pb2.AddRelationshipResponse()
        finally:
            conn.close()

        return graph_pb2.AddRelationshipResponse(message="Relationship added successfully.")

    def GetRelationshipsForTerm(self, request, context):
        logging.info(f"GetRelationshipsForTerm request received for term ID: {request.term_id}")
        conn = get_db_connection(self.db_path)
        
        # Find relationships where the term is either the source or the destination
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM relationships WHERE from_term_id = ? OR to_term_id = ?",
            (request.term_id, request.term_id)
        )
        rows = cursor.fetchall()
        conn.close()

        relationships = [graph_pb2.Relationship(**row) for row in rows]
        return graph_pb2.GetRelationshipsForTermResponse(relationships=relationships)

    def DeleteRelationship(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        return graph_pb2.DeleteRelationshipResponse()