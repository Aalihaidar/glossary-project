"""
gRPC Servicer for the Glossary Service.

Provides methods for managing glossary terms, including creating, retrieving,
updating, and deleting terms from a SQLite database.
"""

import logging
import sqlite3
import uuid

import grpc
from glossary.database import get_db_connection
from proto import glossary_pb2, glossary_pb2_grpc


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    """
    Implements the gRPC GlossaryService.
    """

    def __init__(self, db_path: str):
        """
        Initializes the GlossaryServicer.

        Args:
            db_path: The file path to the SQLite database.
        """
        self.db_path = db_path
        logging.info(f"GlossaryServicer initialized with database at {db_path}")

    def AddTerm(self, request: glossary_pb2.Term, context) -> glossary_pb2.Term:
        """
        Adds a new term to the glossary.

        Checks for required fields and ensures the term does not already exist.

        Args:
            request: A Term object containing the name, definition, and source URL.
            context: The gRPC request context.

        Returns:
            The newly created Term object with its generated ID.
        """
        logging.info(f"AddTerm request received for term: '{request.name}'")
        if not request.name or not request.definition:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term name and definition cannot be empty.")
            return glossary_pb2.Term()

        term_id = str(uuid.uuid4())
        new_term = glossary_pb2.Term(
            id=term_id,
            name=request.name,
            definition=request.definition,
        )

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO terms (id, name, definition) VALUES (?, ?, ?)",
                    (
                        new_term.id,
                        new_term.name,
                        new_term.definition,
                    ),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"Attempted to add a duplicate term: '{request.name}'")
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(
                f"A term with the name '{request.name}' already exists."
            )
            return glossary_pb2.Term()
        except sqlite3.Error as e:
            logging.error(f"Database error during AddTerm: {e}")
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
        """
        Retrieves a single term by its ID.

        Args:
            request: A request containing the `id` of the term to retrieve.
            context: The gRPC request context.

        Returns:
            The found Term object.
        """
        logging.info(f"GetTerm request received for ID: {request.id}")

        if not request.id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID cannot be empty.")
            return glossary_pb2.Term()

        try:
            with get_db_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Allows accessing columns by name
                cursor = conn.cursor()
                term_row = cursor.execute(
                    "SELECT * FROM terms WHERE id = ?", (request.id,)
                ).fetchone()
        except sqlite3.Error as e:
            logging.error(f"Database error during GetTerm: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()

        if term_row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Term with ID '{request.id}' not found.")
            return glossary_pb2.Term()

        return glossary_pb2.Term(**term_row)

    def GetTermByName(
        self, request: glossary_pb2.GetTermByNameRequest, context
    ) -> glossary_pb2.Term:
        """
        Retrieves a single term by its unique name.

        Args:
            request: A request containing the `name` of the term to retrieve.
            context: The gRPC request context.

        Returns:
            The found Term object.
        """
        logging.info(f"GetTermByName request received for name: {request.name}")

        if not request.name:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term name cannot be empty.")
            return glossary_pb2.Term()

        try:
            with get_db_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                term_row = cursor.execute(
                    "SELECT * FROM terms WHERE name = ?", (request.name,)
                ).fetchone()
        except sqlite3.Error as e:
            logging.error(f"Database error during GetTermByName: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()

        if term_row is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Term with name '{request.name}' not found.")
            return glossary_pb2.Term()

        return glossary_pb2.Term(**term_row)

    def SearchTerms(
        self, request: glossary_pb2.SearchTermsRequest, context
    ) -> glossary_pb2.GetAllTermsResponse:
        """
        Searches for terms where the name partially matches a query string.

        Args:
            request: A request containing the search query.
            context: The gRPC request context.

        Returns:
            A response containing a list of all matching Term objects.
        """
        logging.info(f"SearchTerms request received for query: '{request.query}'")

        if not request.query:
            return glossary_pb2.GetAllTermsResponse()

        search_query = f"%{request.query}%"

        try:
            with get_db_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                term_rows = cursor.execute(
                    "SELECT * FROM terms WHERE name LIKE ? ORDER BY name",
                    (search_query,),
                ).fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error during SearchTerms: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.GetAllTermsResponse()

        terms = [glossary_pb2.Term(**row) for row in term_rows]
        return glossary_pb2.GetAllTermsResponse(terms=terms)

    def GetAllTerms(
        self, request: glossary_pb2.GetAllTermsRequest, context
    ) -> glossary_pb2.GetAllTermsResponse:
        """
        Retrieves all terms from the glossary.

        Args:
            request: An empty request object.
            context: The gRPC request context.

        Returns:
            A response containing a list of all Term objects.
        """
        logging.info("GetAllTerms request received")
        try:
            with get_db_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                term_rows = cursor.execute(
                    "SELECT * FROM terms ORDER BY name"
                ).fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error during GetAllTerms: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.GetAllTermsResponse()

        terms = [glossary_pb2.Term(**row) for row in term_rows]
        return glossary_pb2.GetAllTermsResponse(terms=terms)

    def UpdateTerm(self, request: glossary_pb2.Term, context) -> glossary_pb2.Term:
        """
        Updates an existing term in the glossary.

        Args:
            request: A Term object with the `id` of the term to update
                     and the new values for its fields.
            context: The gRPC request context.

        Returns:
            The fully updated Term object.
        """
        logging.info(f"UpdateTerm request received for ID: {request.id}")

        # Input Validation
        if not all([request.id, request.name, request.definition]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID, name, and definition cannot be empty.")
            return glossary_pb2.Term()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                # First, check if the term exists to provide a clear NOT_FOUND error
                existing_term = cursor.execute(
                    "SELECT id FROM terms WHERE id = ?", (request.id,)
                ).fetchone()
                if existing_term is None:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Term with ID '{request.id}' not found.")
                    return glossary_pb2.Term()

                cursor.execute(
                    """
                    UPDATE terms
                    SET name = ?, definition = ?
                    WHERE id = ?
                    """,
                    (request.name, request.definition, request.id),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(
                f"Another term with the name '{request.name}' already exists."
            )
            return glossary_pb2.Term()
        except sqlite3.Error as e:
            logging.error(f"Database error during UpdateTerm: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.Term()

        logging.info(f"Successfully updated term with ID: {request.id}")
        return request

    def DeleteTerm(
        self, request: glossary_pb2.DeleteTermRequest, context
    ) -> glossary_pb2.DeleteTermResponse:
        """
        Deletes a term from the glossary by its ID.

        Args:
            request: A request containing the `id` of the term to delete.
            context: The gRPC request context.

        Returns:
            A response indicating the success of the operation.
        """
        logging.info(f"DeleteTerm request received for ID: {request.id}")

        if not request.id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Term ID cannot be empty.")
            return glossary_pb2.DeleteTermResponse()

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM terms WHERE id = ?", (request.id,))
                conn.commit()

                if cursor.rowcount == 0:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Term with ID '{request.id}' not found.")
                    return glossary_pb2.DeleteTermResponse(success=False)

        except sqlite3.Error as e:
            logging.error(f"Database error during DeleteTerm: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An internal database error occurred: {e}")
            return glossary_pb2.DeleteTermResponse(success=False)

        logging.info(f"Successfully deleted term with ID: {request.id}")
        return glossary_pb2.DeleteTermResponse(success=True)
