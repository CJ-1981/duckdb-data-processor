"""
Characterization Tests for CSV Connector

These tests capture the current behavior of the CSV connector
to ensure behavior preservation during Phase 2 API layer integration.
"""

import pytest
from src.core.connectors.csv import CSVConnector


class TestCSVConnectorCharacterization:
    """
    Characterization tests for CSVConnector behavior

    These tests document existing behavior to prevent regressions
    when integrating with the API layer.
    """

    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create sample CSV file for testing"""
        csv_path = tmp_path / "sample.csv"
        csv_content = """id,name,value
1,Alice,100
2,Bob,200
3,Charlie,300
"""
        csv_path.write_text(csv_content)
        return str(csv_path)

    @pytest.fixture
    def connector(self):
        """Create CSV connector instance"""
        return CSVConnector()

    def test_connector_initialization(self, connector):
        """Characterize: Default connector initialization"""
        assert connector is not None
        assert hasattr(connector, "connect")
        assert hasattr(connector, "read")
        assert hasattr(connector, "validate")
        assert hasattr(connector, "get_metadata")

    def test_connect_to_csv_file(self, connector, sample_csv_file):
        """Characterize: Connection behavior for CSV file"""
        connector.connect(source=sample_csv_file)

        # Connector should successfully connect
        assert True  # No exception raised

    def test_read_csv_data(self, connector, sample_csv_file):
        """Characterize: CSV data reading behavior"""
        connector.connect(source=sample_csv_file)

        rows = list(connector.read(source=sample_csv_file))

        assert len(rows) == 3
        assert rows[0]["id"] == "1"  # CSV reads as strings by default
        assert rows[0]["name"] == "Alice"
        assert rows[0]["value"] == "100"
        assert rows[1]["name"] == "Bob"
        assert rows[2]["name"] == "Charlie"

    def test_read_with_custom_delimiter(self, connector, tmp_path):
        """Characterize: Reading CSV with custom delimiter"""
        csv_path = tmp_path / "semicolon.csv"
        csv_content = """id;name;value
1;Alice;100
2;Bob;200
"""
        csv_path.write_text(csv_content)

        # Create connector with semicolon delimiter
        semicolon_connector = CSVConnector(delimiter=';')
        semicolon_connector.connect(source=str(csv_path))
        rows = list(semicolon_connector.read(source=str(csv_path)))

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"

    def test_validate_valid_csv(self, connector, sample_csv_file):
        """Characterize: Validation behavior for valid CSV"""
        result = connector.validate(source=sample_csv_file)
        assert result is True

    def test_validate_invalid_csv(self, connector, tmp_path):
        """Characterize: Validation behavior for invalid CSV"""
        # CSV connector only validates file path, not content structure
        # This test documents current behavior
        csv_path = tmp_path / "inconsistent.csv"
        csv_path.write_text("id,name\n1,Alice\n2")  # Inconsistent columns

        # Validation only checks file existence and non-empty
        result = connector.validate(source=str(csv_path))
        assert result is True  # Path validation passes

    def test_validate_nonexistent_file(self, connector):
        """Characterize: Validation behavior for nonexistent file"""
        with pytest.raises(FileNotFoundError):
            connector.validate(source="/nonexistent/file.csv")

    def test_get_metadata(self, connector, sample_csv_file):
        """Characterize: Metadata extraction behavior"""
        connector.connect(source=sample_csv_file)
        metadata = connector.get_metadata(source=sample_csv_file)

        assert "row_count" in metadata
        assert metadata["row_count"] == 3
        assert "columns" in metadata
        assert len(metadata["columns"]) == 3
        assert "id" in metadata["columns"]
        assert "name" in metadata["columns"]
        assert "value" in metadata["columns"]

    def test_read_empty_csv(self, connector, tmp_path):
        """Characterize: Reading empty CSV file"""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("id,name,value\n")  # Header only

        connector.connect(source=str(csv_path))
        rows = list(connector.read(source=str(csv_path)))

        assert len(rows) == 0

    def test_read_csv_with_quotes(self, connector, tmp_path):
        """Characterize: Reading CSV with quoted fields"""
        csv_path = tmp_path / "quoted.csv"
        csv_content = '''id,name,description
1,"Alice, Smith","Developer, with, commas"
2,"Bob","Manager"
'''
        csv_path.write_text(csv_content)

        connector.connect(source=str(csv_path))
        rows = list(connector.read(source=str(csv_path)))

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice, Smith"
        assert rows[0]["description"] == "Developer, with, commas"

    def test_read_csv_with_different_encodings(self, connector, tmp_path):
        """Characterize: Reading CSV with different encodings"""
        csv_path = tmp_path / "encoded.csv"
        csv_content = "id,name\n1,Alice\n2,Bob\n"
        csv_path.write_bytes(csv_content.encode("utf-8"))

        # Create connector with UTF-8 encoding
        utf8_connector = CSVConnector(encoding='utf-8')
        utf8_connector.connect(source=str(csv_path))
        rows = list(utf8_connector.read(source=str(csv_path)))

        assert len(rows) == 2

    def test_base_connector_interface_compliance(self, connector):
        """Characterize: Compliance with BaseConnector interface"""
        from src.core.connectors.base import BaseConnector

        assert isinstance(connector, BaseConnector)
        assert hasattr(connector, "connect")
        assert hasattr(connector, "read")
        assert hasattr(connector, "validate")
        assert hasattr(connector, "get_metadata")
