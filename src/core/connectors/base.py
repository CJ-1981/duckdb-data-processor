"""
Base Connector Interface

Defines the abstract interface for all data connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Iterator


# @MX:ANCHOR: Base connector inheritance (fan_in >= 3: CSV, Database, API connectors)
# @MX:REASON: Abstract interface defines contract for all data source connectors
# @MX:SPEC: SPEC-PLATFORM-001 Module 1: Data Connectors
class BaseConnector(ABC):
    """
    Abstract base class for data connectors

    All connectors must implement these methods for data ingestion
    into the DuckDB data processing platform.
    """

    def __init__(self):
        """Initialize connector with default configuration"""
        pass

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Establish connection to data source

        Args:
            **kwargs: Connection parameters
        """
        pass

    @abstractmethod
    def read(self, source: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read data from source

        Args:
            source: Data source identifier (file path, URL, etc.)
            **kwargs: Additional read options

        Yields:
            Dictionary representing a single row/record
        """
        pass

    @abstractmethod
    def validate(self, source: str, **kwargs) -> bool:
        """
        Validate data source configuration

        Args:
            source: Data source to validate
            **kwargs: Additional validation options

        Returns:
            True if valid, raises exception otherwise
        """
        pass

    @abstractmethod
    def get_metadata(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Get metadata about data source

        Args:
            source: Data source to get metadata from
            **kwargs: Additional metadata options

        Returns:
            Dictionary with metadata (row count, columns, etc.)
        """
        pass
