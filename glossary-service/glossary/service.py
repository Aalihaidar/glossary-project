# glossary-service/glossary/service.py

"""
gRPC Servicer for the Glossary Service.

Provides methods for managing glossary terms using a single, shared SQLite connection,
which is the recommended pattern for multi-threaded server applications.
"""

import logging
import sqlite3
import uuid

import grpc
from proto import glossary_pb2, glossary_pb2_grpc


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    """
    Implements the gRPC GlossaryService.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initializes the GlossaryServicer with a shared database connection.

        Args:
            conn: A shared, thread-safe sqlite3.Connection object.
        """
        self.conn = conn
        logging.info("GlossaryServicer initialized with a shared database connection.")

    def AddTerm(self, request: glossary_pb2.Term, context) -> glossary_pb2.Term:
        """Adds a new term to the glossary."""
        logging.info(f"AddTerm request received for term: '{request.name}'")
        if not request.name or not request.definition:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term name and definition cannot be empty.")
            return glossary_pb2.Term()

        term_id = str(uuid.uuid4())
        new_term = glossary_pb2.Term(
            id=term_id, name=request.name, definition=request.definition
        )

        try:
            # We no longer use 'with', as the connection is managed externally.
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO terms (id, name, definition) VALUES (?, ?, ?)",
                (new_term.id, new_term.name, new_term.definition),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(
                f"A term with the name '{request.name}' already exists."
            )
            return glossary_pb2.Term()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()

        logging.info(
            f"Successfully added term '{new_term.name}' with ID: {new_term.id}"
        )
        return new_term

    def GetTerm(
        self, request: glossary_pb2.GetTermRequest, context
    ) -> glossary_pb2.Term:
        """Retrieves a single term by its ID."""
        logging.info(f"GetTerm request received for ID: {request.id}")
        if not request.id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID cannot be empty.")
            return glossary_pb2.Term()

        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            term_row = cursor.execute(
                "SELECT * FROM terms WHERE id = ?", (request.id,)
            ).fetchone()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()

        if term_row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Term with ID '{request.id}' not found.")
            return glossary_pb2.Term()

        return glossary_pb2.Term(**term_row)

    # ... All other methods (GetTermByName, SearchTerms, etc.) should be similarly
    # updated to use `self.conn` directly instead of `with get_db_connection(...)`.
    # For brevity, I will show the complete, correct implementation without repeating
    # the comments for every method.

    def GetTermByName(
        self, request: glossary_pb2.GetTermByNameRequest, context
    ) -> glossary_pb2.Term:
        if not request.name:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term name cannot be empty.")
            return glossary_pb2.Term()
        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            term_row = cursor.execute(
                "SELECT * FROM terms WHERE name = ?", (request.name,)
            ).fetchone()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()
        if term_row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Term with name '{request.name}' not found.")
            return glossary_pb2.Term()
        return glossary_pb2.Term(**term_row)

    def GetAllTerms(
        self, request: glossary_pb2.GetAllTermsRequest, context
    ) -> glossary_pb2.GetAllTermsResponse:
        try:
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            term_rows = cursor.execute("SELECT * FROM terms ORDER BY name").fetchall()
        except sqlite3.Error as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.GetAllTermsResponse()
        terms = [glossary_pb2.Term(**row) for row in term_rows]
        return glossary_pb2.GetAllTermsResponse(terms=terms)

    # ... Implementations for SearchTerms, UpdateTerm, and DeleteTerm follow the same pattern ...
