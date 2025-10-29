import sys
sys.path.append('proto')

import logging  # noqa: E402
import uuid  # noqa: E402
import grpc  # noqa: E402
from proto import glossary_pb2, glossary_pb2_grpc  # noqa: E402
from glossary.database import get_db_connection  # noqa: E402


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    def __init__(self, db_path):
        self.db_path = db_path

    def AddTerm(self, request, context):
        logging.info(f"AddTerm request received for term: {request.name}")
        conn = get_db_connection(self.db_path)
        term_id = str(uuid.uuid4())

        try:
            conn.execute(
                "INSERT INTO terms (id, name, definition, source_url) "
                "VALUES (?, ?, ?, ?)",
                (term_id, request.name, request.definition, request.source_url),
            )
            conn.commit()
        except conn.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {e}")
            return glossary_pb2.Term()
        finally:
            conn.close()

        return glossary_pb2.Term(
            id=term_id,
            name=request.name,
            definition=request.definition,
            source_url=request.source_url,
        )

    def GetTerm(self, request, context):
        logging.info(f"GetTerm request received for ID: {request.id}")
        conn = get_db_connection(self.db_path)
        term_row = conn.execute(
            "SELECT * FROM terms WHERE id = ?", (request.id,)
        ).fetchone()
        conn.close()

        if term_row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Term not found.")
            return glossary_pb2.Term()

        return glossary_pb2.Term(**term_row)

    def GetAllTerms(self, request, context):
        logging.info("GetAllTerms request received")
        conn = get_db_connection(self.db_path)
        terms_rows = conn.execute("SELECT * FROM terms").fetchall()
        conn.close()

        terms = [glossary_pb2.Term(**row) for row in terms_rows]
        return glossary_pb2.GetAllTermsResponse(terms=terms)

    def UpdateTerm(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        return glossary_pb2.Term()

    def DeleteTerm(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        return glossary_pb2.DeleteTermResponse()
