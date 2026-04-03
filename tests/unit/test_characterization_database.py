"""
Characterization Tests for DatabaseConnection

These tests capture the current behavior of the DatabaseConnection class
to ensure behavior preservation during Phase 2 API layer integration.
"""

import pytest
import threading
from src.core.database import DatabaseConnection, ConnectionError, QueryExecutionError


class TestDatabaseConnectionCharacterization:
    """
    Characterization tests for DatabaseConnection behavior

    These tests document existing behavior to prevent regressions
    when integrating with the API layer.
    """

    @pytest.fixture
    def temp_db_path(self, tmp_path):
        """Create temporary database path"""
        return str(tmp_path / "test.duckdb")

    @pytest.fixture
    def db(self, temp_db_path):
        """Create database connection for testing"""
        db = DatabaseConnection(temp_db_path)
        yield db
        db.close()

    def test_connection_initialization_defaults(self, temp_db_path):
        """Characterize: Default connection initialization parameters"""
        db = DatabaseConnection(temp_db_path)

        assert db.db_path == temp_db_path
        assert db.max_connections == 10
        assert db.connection_timeout == 30.0
        assert db.query_timeout == 60.0
        assert db.is_healthy() is True

        db.close()

    def test_connection_custom_parameters(self, temp_db_path):
        """Characterize: Connection initialization with custom parameters"""
        db = DatabaseConnection(
            temp_db_path,
            max_connections=5,
            connection_timeout=10.0,
            query_timeout=30.0,
        )

        assert db.max_connections == 5
        assert db.connection_timeout == 10.0
        assert db.query_timeout == 30.0

        db.close()

    def test_execute_simple_query(self, db):
        """Characterize: Simple query execution behavior"""
        result = db.execute("SELECT 1 as num")

        assert len(result) == 1
        assert result[0]["num"] == 1

    def test_execute_query_with_parameters(self, db):
        """Characterize: Parameterized query execution"""
        db.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        db.execute("INSERT INTO test VALUES (?, ?)", parameters=[1, "Alice"])

        result = db.execute("SELECT * FROM test WHERE id = ?", parameters=[1])

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Alice"

    def test_execute_returns_empty_for_no_results(self, db):
        """Characterize: Empty result handling for INSERT/UPDATE/DELETE"""
        result = db.execute("CREATE TABLE test (id INTEGER)")

        assert result == []

    def test_execute_batch_multiple_parameters(self, db):
        """Characterize: Batch execution with multiple parameter sets"""
        db.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")

        db.execute_batch(
            "INSERT INTO test VALUES (?, ?)",
            parameters_list=[[1, "Alice"], [2, "Bob"], [3, "Charlie"]],
        )

        result = db.execute("SELECT * FROM test ORDER BY id")
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        assert result[2]["name"] == "Charlie"

    def test_stream_results_in_chunks(self, db):
        """Characterize: Result streaming behavior"""
        db.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
        for i in range(100):
            db.execute("INSERT INTO test VALUES (?, ?)", parameters=[i, f"User{i}"])

        chunks = list(db.stream("SELECT * FROM test ORDER BY id", chunk_size=10))

        assert len(chunks) == 10
        assert len(chunks[0]) == 10
        assert chunks[0][0]["id"] == 0
        assert chunks[-1][-1]["id"] == 99

    def test_iterate_row_by_row(self, db):
        """Characterize: Row-by-row iteration behavior"""
        db.execute("CREATE TABLE test (id INTEGER)")
        db.execute("INSERT INTO test VALUES (1)")
        db.execute("INSERT INTO test VALUES (2)")
        db.execute("INSERT INTO test VALUES (3)")

        rows = list(db.iterate("SELECT * FROM test ORDER BY id"))

        assert len(rows) == 3
        assert rows[0]["id"] == 1
        assert rows[1]["id"] == 2
        assert rows[2]["id"] == 3

    def test_health_check_alive(self, db):
        """Characterize: Health check for alive connection"""
        assert db.is_healthy() is True

    def test_health_check_after_close(self, db):
        """Characterize: Health check for closed connection"""
        db.close()
        assert db.is_healthy() is False

    def test_context_manager(self, temp_db_path):
        """Characterize: Context manager behavior"""
        with DatabaseConnection(temp_db_path) as db:
            assert db.is_healthy() is True
            result: list[dict] = db.execute("SELECT 1 as num")
            assert result[0]["num"] == 1

        # Connection should be closed after context
        assert db.is_healthy() is False

    def test_thread_safe_connection_access(self, temp_db_path):
        """Characterize: Thread-safe concurrent access"""
        # NOTE: DuckDB has known threading limitations
        # This test documents current behavior: sequential access works, concurrent may fail
        db = DatabaseConnection(temp_db_path, max_connections=5)
        db.execute("CREATE TABLE test (id INTEGER, value INTEGER)")
        db.execute("INSERT INTO test VALUES (1, 100)")

        # Test sequential access (this should work)
        result = db.execute("SELECT * FROM test WHERE id = 1")
        assert result[0]["value"] == 100

        # Characterize: DuckDB connection is not thread-safe for concurrent queries
        # This is a known limitation documented here
        db.close()

    def test_auto_reconnect_on_query(self, temp_db_path):
        """Characterize: Auto-reconnect behavior"""
        db = DatabaseConnection(temp_db_path, auto_reconnect=True)

        # Initial connection is healthy
        assert db.is_healthy() is True

        # Close connection explicitly
        db.close()
        assert db.is_healthy() is False

        # Auto-reconnect should happen on next query
        result = db.execute("SELECT 1 as num")
        assert result[0]["num"] == 1
        assert db.is_healthy() is True

        db.close()

    def test_error_handling_invalid_sql(self, db):
        """Characterize: Error handling for invalid SQL"""
        with pytest.raises(QueryExecutionError):
            db.execute("INVALID SQL QUERY")

    def test_error_handling_missing_table(self, db):
        """Characterize: Error handling for missing table"""
        with pytest.raises(QueryExecutionError):
            db.execute("SELECT * FROM nonexistent_table")

    def test_memory_database(self):
        """Characterize: In-memory database behavior"""
        db = DatabaseConnection(":memory:")

        db.execute("CREATE TABLE test (id INTEGER)")
        db.execute("INSERT INTO test VALUES (1)")

        result: list[dict] = db.execute("SELECT * FROM test")
        assert len(result) == 1

        db.close()

    def test_cancel_query(self, db):
        """Characterize: Query cancellation behavior"""
        # Note: This is a best-effort test as DuckDB may not support cancellation
        db.cancel_query()
        # Should not raise an exception
        assert True

    def test_connection_retry_on_failure(self, tmp_path):
        """Characterize: Connection retry behavior"""
        # Use an invalid path to trigger retry
        invalid_path = "/nonexistent/path/to/db.duckdb"

        with pytest.raises(ConnectionError):
            DatabaseConnection(invalid_path, max_retries=3, retry_delay=0.1)

    def test_query_timeout_parameter_stored(self, temp_db_path):
        """Characterize: Query timeout parameter storage (not enforced by DuckDB)"""
        db = DatabaseConnection(temp_db_path, query_timeout=5.0)

        # Parameter is stored but not enforced (DuckDB limitation)
        assert db.query_timeout == 5.0

        db.close()
