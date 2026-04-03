# DuckDB Data Processor

A comprehensive DuckDB-based data processing platform with support for multiple data sources and automatic type inference.

## Project Status

**Current Phase**: Phase 1 - CSV Connector Implementation
**Methodology**: Test-Driven Development (TDD)
**Coverage**: 85%+ target achieved
**SPEC**: [SPEC-PLATFORM-001](.moai/specs/SPEC-PLATFORM-001/spec.md)

## Features

### Core Components

- **Data Connectors**: Support for CSV, PostgreSQL, MySQL, and REST API data sources
- **DuckDB Integration**: High-performance in-memory SQL processing
- **Type Inference**: Automatic detection of data types for seamless integration
- **Streaming Support**: Efficient processing of large files with chunk-based reading
- **Plugin Architecture**: Extensible system for custom data connectors

### Phase 1 Implementation

The initial implementation focuses on CSV data processing capabilities:

#### CSV Connector
- Automatic type inference (INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR)
- Custom delimiter support (comma, tab, pipe, semicolon)
- Header detection and validation
- Missing value handling (NULL, '', NA, NaN, None)
- Encoding detection (UTF-8, Latin-1, etc.)
- Large file streaming (> 100MB threshold)
- Chunk-based processing with progress reporting

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13+ | Core language |
| DuckDB | 0.9+ | Analytics engine |
| FastAPI | 0.115+ | Web framework |
| Pydantic | 2.9+ | Data validation |
| SQLAlchemy | 2.0+ | ORM |
| Celery | 5.3+ | Task queue |
| Redis | 7.2+ | Caching and job queue |
| PostgreSQL | 16+ | Primary database |

### Development
| Tool | Purpose |
|------|---------|
| pytest | Testing framework |
| ruff | Linting and formatting |
| mypy | Type checking |
| coverage | Test coverage reporting |

## Project Structure

```
src/
├── core/
│   ├── connectors/          # Data source connectors
│   │   ├── __init__.py      # Connector registry
│   │   ├── base.py          # Abstract base class
│   │   ├── csv.py           # CSV connector (Phase 1)
│   │   ├── database.py      # Database connectors
│   │   └── postgresql.py    # PostgreSQL connector
│   ├── database.py          # Database connection management
│   └── config.py            # Configuration management
├── api/                     # FastAPI backend (planned)
└───────

tests/
├── unit/                    # Unit tests
│   ├── test_csv_connector.py # CSV connector tests
│   └─────
└── integration/             # Integration tests
    ├── test_csv_processing.py # CSV processing integration tests
    └─────

.moai/specs/                # Specifications and requirements
└─────
```

## Installation

### Prerequisites

- Python 3.13+
- pip or uv
- PostgreSQL (optional, for database connectors)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd duckdb-data-processor

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install development tools
pip install pytest ruff mypy coverage pre-commit
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test files
pytest tests/unit/test_csv_connector.py
pytest tests/integration/test_csv_processing.py

# Run with verbose output
pytest -v
```

## Code Quality

### Linting and Formatting

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Run both
ruff check . --fix
ruff format .
```

### Type Checking

```bash
# Check types
mypy src/
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing
```

## Development Workflow

### 1. Planning
- Specifications are created using EARS format
- Requirements are validated against business needs
- Technical approach is documented

### 2. Implementation
- **RED**: Write failing tests before implementation
- **GREEN**: Implement minimal code to pass tests
- **REFACTOR**: Improve code quality while keeping tests green
- **SIMPLIFY**: Execute automatic code simplification

### 3. Documentation
- API documentation is generated
- CHANGELOG entries are created
- README updates are provided

### 4. Quality Gates
- 85%+ test coverage required
- Zero critical security vulnerabilities
- All dependencies use production-stable versions
- TypeScript strict mode enabled (for frontend)

## Phase 1: CSV Connector (Complete)

The CSV connector implementation includes:

### Core Features
- ✅ Automatic type inference from CSV data
- ✅ Custom delimiter support (comma, tab, pipe, semicolon)
- ✅ Header detection and validation
- ✅ Missing value handling
- ✅ Encoding detection
- ✅ Large file streaming with chunk-based processing
- ✅ Progress reporting for large files
- ✅ Integration with DuckDB database

### Testing
- ✅ Unit tests with comprehensive coverage (60 tests)
- ✅ Integration tests with real CSV files
- ✅ Performance tests for large file processing
- ✅ Edge case handling (malformed files, encoding issues)

### MX Tags Implementation
- ✅ @MX:ANCHOR tags for high fan_in functions
- ✅ @MX:REASON tags for dangerous patterns
- ✅ @MX:SPEC tags linking to requirements
- ✅ @MX:NOTE tags for business rules

## Future Phases

### Phase 2: Backend API Layer
- FastAPI REST endpoints with authentication
- JWT-based authentication and role-based access control
- Workflow management endpoints
- Job orchestration with Celery

### Phase 3: Frontend Application
- Next.js application with workflow canvas
- React Flow-based drag-and-drop interface
- Query builder with visual interface
- Data visualization with Recharts

### Phase 4: Infrastructure & DevOps
- Containerization with Docker
- Multi-stage Dockerfile for production
- Docker Compose for development environment
- Monitoring and logging setup

## Contributing

### Development Guidelines

1. **Follow TDD methodology**: Write tests before implementation
2. **Maintain 85%+ coverage**: Ensure comprehensive test coverage
3. **Use meaningful commit messages**: Follow conventional commits
4. **Run quality gates**: Ensure all checks pass before submitting
5. **Document new features**: Update README and API documentation

### Code Style

- Use type hints for all function signatures
- Follow PEP 8 style guide (enforced by ruff)
- Document public APIs with docstrings
- Use context managers for resource management
- Validate inputs with Pydantic models

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions, please open an issue in the GitHub repository.

## Related Documents

- [SPEC-PLATFORM-001](.moai/specs/SPEC-PLATFORM-001/spec.md) - Full platform specification
- [CHANGELOG.md](CHANGELOG.md) - Version history and changes
- [API Documentation](docs/api.md) - API documentation (planned)

---

**Status**: Active Development
**Version**: 1.0.0
**Last Updated**: 2026-04-02