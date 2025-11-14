"""Shannon CLI V3.0 Test Configuration

Pytest configuration for Shannon CLI testing with NO MOCKS philosophy.

Key Principles:
1. Functional tests use real SDK, real Serena, real filesystem
2. Integration tests validate actual component interactions
3. Unit tests only for pure functions (mathematical, parsing)
4. NO mocking of external dependencies

Test Markers:
- @pytest.mark.functional: End-to-end tests with real components
- @pytest.mark.integration: Module integration tests
- @pytest.mark.unit: Pure function unit tests
- @pytest.mark.slow: Long-running tests (>10s)
- @pytest.mark.requires_sdk: Requires Claude Agent SDK
- @pytest.mark.requires_serena: Requires Serena MCP
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, AsyncGenerator
import logging

# Import Shannon components
from shannon.config import ShannonConfig
from shannon.sdk.client import ShannonSDKClient
from shannon.orchestrator import ContextAwareOrchestrator
from shannon.cache.manager import CacheManager
from shannon.analytics.database import AnalyticsDatabase


# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "functional: End-to-end functional tests (NO MOCKS)"
    )
    config.addinivalue_line(
        "markers", "integration: Module integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: Pure function unit tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >10 seconds"
    )
    config.addinivalue_line(
        "markers", "requires_sdk: Requires Claude Agent SDK"
    )
    config.addinivalue_line(
        "markers", "requires_serena: Requires Serena MCP"
    )


# Pytest-asyncio configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test directories
@pytest.fixture(scope="session")
def test_root() -> Path:
    """Root directory for all test files"""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def fixtures_dir(test_root: Path) -> Path:
    """Directory containing test fixtures"""
    return test_root / "fixtures"


@pytest.fixture(scope="session")
def sample_specs_dir(fixtures_dir: Path) -> Path:
    """Directory containing sample specifications"""
    return fixtures_dir / "sample_specs"


@pytest.fixture(scope="session")
def sample_codebases_dir(fixtures_dir: Path) -> Path:
    """Directory containing sample codebases for context testing"""
    return fixtures_dir / "sample_codebases"


# Temporary test environment
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test isolation"""
    temp_path = Path(tempfile.mkdtemp(prefix="shannon_test_"))
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_config_dir(temp_dir: Path) -> Path:
    """Temporary Shannon config directory"""
    config_dir = temp_dir / ".shannon"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def test_config(temp_config_dir: Path) -> ShannonConfig:
    """Test Shannon configuration with isolated directories"""
    config = ShannonConfig()
    # Override config directory to isolated temp directory
    config.config_dir = temp_config_dir
    return config


# Cache fixtures
@pytest.fixture
def test_cache_manager(temp_config_dir: Path) -> CacheManager:
    """Test CacheManager with isolated cache directory"""
    cache_dir = temp_config_dir / "cache"
    return CacheManager(base_dir=cache_dir)


# Analytics fixtures
@pytest.fixture
def test_analytics_db(temp_config_dir: Path) -> AnalyticsDatabase:
    """Test AnalyticsDatabase with isolated database"""
    db_path = temp_config_dir / "test_analytics.db"
    return AnalyticsDatabase(db_path=db_path)


# SDK Client fixtures (REAL SDK, NO MOCKS)
@pytest.fixture
def sdk_client() -> Generator[ShannonSDKClient, None, None]:
    """Real ShannonSDKClient for functional tests

    NO MOCKING - Uses actual Claude Agent SDK
    Tests marked with @pytest.mark.requires_sdk will skip if SDK unavailable
    """
    try:
        client = ShannonSDKClient(enable_v3_features=True)
        yield client
    except (ImportError, FileNotFoundError) as e:
        pytest.skip(f"SDK not available: {e}")


# Orchestrator fixtures
@pytest.fixture
def test_orchestrator(test_config: ShannonConfig) -> ContextAwareOrchestrator:
    """Test ContextAwareOrchestrator with isolated config"""
    return ContextAwareOrchestrator(config=test_config)


# Sample data fixtures
@pytest.fixture
def simple_spec() -> str:
    """Simple specification for basic testing"""
    return """
# Add User Authentication

Implement basic email/password authentication:
- User registration endpoint
- Login endpoint
- JWT token generation
- Password hashing with bcrypt

Estimated: 2-3 days
"""


@pytest.fixture
def complex_spec() -> str:
    """Complex specification for stress testing"""
    return """
# Build Real-Time Analytics Dashboard

Implement comprehensive analytics platform:

## Backend Services
- WebSocket server for real-time data streaming
- Time-series database (TimescaleDB)
- Data aggregation pipeline
- Caching layer (Redis)
- API rate limiting

## Frontend Dashboard
- React with TypeScript
- Real-time charts (D3.js)
- Responsive layout
- Dark mode support

## DevOps
- Docker containerization
- Kubernetes deployment
- CI/CD pipeline
- Monitoring and alerting

## Security
- HTTPS/TLS
- OAuth2 integration
- Rate limiting
- Input validation

Estimated: 3-4 weeks
Requires: Database, DevOps, Frontend, Backend expertise
"""


@pytest.fixture
def sample_project_structure(temp_dir: Path) -> Path:
    """Create sample project structure for context testing"""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir()

    # Create basic project structure
    (project_dir / "src").mkdir()
    (project_dir / "src" / "auth.js").write_text("""
// JWT authentication module
function login(email, password) {
    // Validate credentials
    // Generate JWT token
    return generateToken({email});
}

function register(email, password) {
    // Hash password
    // Create user record
    return createUser({email, password});
}
""")

    (project_dir / "src" / "api.js").write_text("""
// REST API endpoints
const express = require('express');
const router = express.Router();

router.post('/login', async (req, res) => {
    // Login handler
});

router.post('/register', async (req, res) => {
    // Registration handler
});
""")

    (project_dir / "package.json").write_text("""
{
    "name": "sample-project",
    "version": "1.0.0",
    "dependencies": {
        "express": "^4.18.0",
        "jsonwebtoken": "^9.0.0",
        "bcrypt": "^5.1.0"
    }
}
""")

    return project_dir


# Helper functions for tests
def assert_analysis_result_valid(result: dict) -> None:
    """Assert that analysis result has required structure

    Args:
        result: Analysis result dictionary

    Raises:
        AssertionError: If result structure is invalid
    """
    # Required top-level keys
    assert 'complexity_score' in result, "Missing complexity_score"
    assert 'interpretation' in result, "Missing interpretation"
    assert 'dimension_scores' in result, "Missing dimension_scores"
    assert 'domains' in result, "Missing domains"

    # Validate complexity score
    score = result['complexity_score']
    assert 0.0 <= score <= 1.0, f"Invalid complexity score: {score}"

    # Validate interpretation
    valid_interpretations = {'simple', 'moderate', 'complex', 'very_complex'}
    interp = result['interpretation'].lower()
    assert any(v in interp for v in valid_interpretations), \
        f"Invalid interpretation: {result['interpretation']}"

    # Validate dimensions (8 expected)
    dimensions = result['dimension_scores']
    assert len(dimensions) >= 6, f"Expected at least 6 dimensions, got {len(dimensions)}"

    # Validate domains (percentages sum to 100)
    domains = result['domains']
    if domains:
        total = sum(domains.values())
        assert 95 <= total <= 105, f"Domain percentages sum to {total}, expected ~100"


def assert_metrics_collected(snapshot: dict) -> None:
    """Assert that metrics snapshot has expected data

    Args:
        snapshot: MetricsSnapshot dictionary

    Raises:
        AssertionError: If metrics are invalid
    """
    assert 'message_count' in snapshot
    assert snapshot['message_count'] > 0, "No messages collected"

    # Should have timing data
    assert 'duration_seconds' in snapshot
    assert snapshot['duration_seconds'] >= 0.0

    # Should have cost/token data (may be 0 for some operations)
    assert 'cost_usd' in snapshot
    assert 'tokens_input' in snapshot
    assert 'tokens_output' in snapshot


# Skip conditions
def skip_if_no_sdk():
    """Skip test if Claude Agent SDK not available"""
    try:
        from claude_agent_sdk import query
        return False
    except ImportError:
        return True


def skip_if_no_serena():
    """Skip test if Serena MCP not available"""
    # TODO: Implement Serena availability check
    return False


# Pytest hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add skip conditions"""
    skip_sdk = pytest.mark.skip(reason="Claude Agent SDK not available")
    skip_serena = pytest.mark.skip(reason="Serena MCP not available")

    for item in items:
        # Skip SDK-dependent tests if SDK unavailable
        if "requires_sdk" in item.keywords and skip_if_no_sdk():
            item.add_marker(skip_sdk)

        # Skip Serena-dependent tests if Serena unavailable
        if "requires_serena" in item.keywords and skip_if_no_serena():
            item.add_marker(skip_serena)
