import sys

sys.path.append("proto")

import logging  # noqa: E402
import grpc  # noqa: E402
from proto import graph_pb2, graph_pb2_grpc  # noqa: E402
from graph.database import get_db_connection  # noqa: E402


class GraphServicer(graph_pb2_grpc.GraphServiceServicer):
    """Implements the gRPC Graph Service."""

    def __init__(self, db_path):
        self.db_path = db_path

    def AddRelationship(self, request, context):
        logging.info(
            f"AddRelationship request: {request.from_term_id} "
            f"-> {request.to_term_id}"
        )
        conn = get_db_connection(self.db_path)

        try:
            conn.execute(
                "INSERT INTO relationships (from_term_id, to_term_id, type) "
                "VALUES (?, ?, ?)",
                (request.from_term_id, request.to_term_id, request.type),
            )
            conn.commit()
        except conn.IntegrityError:
            msg = "Relationship already exists."
            logging.warning(msg)
            return graph_pb2.AddRelationshipResponse(message=msg)
        except conn.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return graph_pb2.AddRelationshipResponse()
        finally:
            conn.close()

        return graph_pb2.AddRelationshipResponse(
            message="Relationship added successfully."
        )

    def GetRelationshipsForTerm(self, request, context):
        logging.info(f"GetRelationshipsForTerm request for term ID: {request.term_id}")
        conn = get_db_connection(self.db_path)

        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM relationships WHERE from_term_id = ? OR to_term_id = ?",
            (request.term_id, request.term_id),
        )
        rows = cursor.fetchall()
        conn.close()

        relationships = [graph_pb2.Relationship(**row) for row in rows]
        return graph_pb2.GetRelationshipsForTermResponse(relationships=relationships)

    def DeleteRelationship(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        return graph_pb2.DeleteRelationshipResponse()
