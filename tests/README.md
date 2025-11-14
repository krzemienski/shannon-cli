# Shannon CLI V3.0 Test Suite

**Philosophy: NO MOCKS**

All Shannon CLI tests follow the "NO MOCKS" philosophy from the Shannon Framework:
- Functional tests use real SDK, real filesystem, real databases
- Integration tests validate actual component interactions
- Unit tests only for pure functions (mathematical, parsing)
- NO mocking of external dependencies

## Architecture

Tests are organized by type following the V3 architecture document:

```
tests/
├── conftest.py              # Pytest configuration & fixtures
├── functional/              # End-to-end functional tests (NO MOCKS)
│   ├── test_sdk_interception.py
│   ├── test_metrics_system.py
│   └── test_cache_system.py
├── integration/             # Module integration tests
│   └── test_orchestrator_integration.py
├── unit/                    # Pure function unit tests
│   └── test_cost_optimization.py
└── fixtures/                # Test data & sample files
    ├── sample_specs/
    ├── sample_codebases/
    └── sample_responses/
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run by type
```bash
# Functional tests only
pytest -m functional

# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit

# Fast tests (exclude slow tests)
pytest -m "not slow"
```

### Run by module
```bash
# SDK interception tests
pytest tests/functional/test_sdk_interception.py

# Cache system tests
pytest tests/functional/test_cache_system.py

# Orchestrator integration
pytest tests/integration/test_orchestrator_integration.py
```

### Run specific test
```bash
pytest tests/functional/test_sdk_interception.py::test_interceptor_zero_latency
```

### Run with coverage
```bash
pytest --cov=src/shannon --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run in parallel (faster)
```bash
pytest -n auto
```

## Test Markers

Tests are marked with categories:

- `@pytest.mark.functional` - End-to-end tests with real components
- `@pytest.mark.integration` - Module integration tests
- `@pytest.mark.unit` - Pure function tests
- `@pytest.mark.slow` - Tests taking >10 seconds
- `@pytest.mark.requires_sdk` - Requires Claude Agent SDK
- `@pytest.mark.requires_serena` - Requires Serena MCP

## Test Categories

### Functional Tests (NO MOCKS)

Functional tests validate Shannon CLI behavior with **real** components:
- Real Claude Agent SDK calls
- Real filesystem operations
- Real SQLite databases
- Real Serena MCP integration

These tests may:
- Take longer to run
- Require external dependencies
- Cost API tokens (minimal)

**Example**: `test_sdk_interception.py::test_interceptor_with_real_sdk`

### Integration Tests

Integration tests validate that Shannon CLI subsystems work together:
- Context + Cache integration
- Metrics + Analytics integration
- Cost Optimizer + Budget Enforcer coordination
- Full ContextAwareOrchestrator workflows

**Example**: `test_orchestrator_integration.py::test_analysis_workflow_with_cache`

### Unit Tests

Unit tests validate pure functions with NO I/O:
- Cost calculations
- Model selection logic
- Budget math
- Parsing and formatting

**Example**: `test_cost_optimization.py::test_model_selector_simple_task`

## Writing New Tests

### Functional Test Template

```python
@pytest.mark.functional
@pytest.mark.asyncio
async def test_my_feature(temp_dir, test_config):
    """
    Test my feature with real components

    NO MOCKS - uses actual filesystem, database, etc.

    Validates:
    - Feature works end-to-end
    - Real component interactions
    """
    # Setup with real components
    cache = CacheManager(base_dir=temp_dir / "cache")

    # Execute real operation
    result = await real_function()

    # Verify with assertions
    assert result is not None
    assert result.success == True
```

### Integration Test Template

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_component_integration(test_orchestrator):
    """
    Test components A and B work together

    Validates:
    - Data flows from A to B
    - State synchronized
    - Integration point correct
    """
    # Use real orchestrator
    result = await test_orchestrator.execute_task(...)

    # Verify integration
    assert result['component_a'] is not None
    assert result['component_b'] is not None
```

### Unit Test Template

```python
@pytest.mark.unit
def test_pure_function():
    """
    Test pure function calculation

    Unit test - NO I/O, NO mocks needed
    """
    result = calculate_something(input_value)

    assert result == expected_value
```

## Test Fixtures

Common fixtures available (see `conftest.py`):

- `temp_dir` - Temporary directory (cleaned after test)
- `test_config` - Isolated Shannon configuration
- `test_cache_manager` - CacheManager with temp cache
- `test_analytics_db` - AnalyticsDatabase with temp DB
- `test_orchestrator` - Full ContextAwareOrchestrator
- `sdk_client` - Real ShannonSDKClient (if SDK available)
- `simple_spec` - Sample simple specification
- `complex_spec` - Sample complex specification
- `sample_project_structure` - Sample codebase for context tests

## Coverage Requirements

Test coverage targets from architecture document:

- **Overall**: 70% minimum
- **Critical paths**: 90% minimum
- **New V3 modules**: 80% minimum

### Coverage by module:
- `metrics/`: 75% (UI code hard to test)
- `cache/`: 85% (pure logic, high testability)
- `mcp/`: 80% (depends on external MCPs)
- `agents/`: 75% (concurrent code complex)
- `optimization/`: 90% (mostly pure functions)
- `analytics/`: 85% (database queries)
- `context/`: 80% (file I/O heavy)
- `orchestrator.py`: 70% (integration code)

## CI/CD Integration

### Pre-commit
```bash
# Run fast tests only
pytest -m "unit and not slow"
```

### Pull Request
```bash
# Run unit + integration + quick functional
pytest -m "not slow" --cov=src/shannon
```

### Nightly
```bash
# Full test suite including slow tests
pytest --cov=src/shannon
```

### Release
```bash
# Full suite + performance benchmarks
pytest --cov=src/shannon --cov-fail-under=70
```

## Debugging Failed Tests

### Run with output
```bash
pytest -s  # Don't capture stdout
pytest -vv # Extra verbose
```

### Run with debugger
```bash
pytest --pdb  # Drop into debugger on failure
```

### Run single test with logging
```bash
pytest tests/path/to/test.py::test_name -vv -s --log-cli-level=DEBUG
```

### Check test output
```bash
cat tests/test_run.log  # Detailed log file
```

## Performance Benchmarks

Some tests include performance assertions:

- SDK interception: <100ms overhead per 1000 messages
- Cache hit: <10ms retrieval
- Metrics collection: >1000 messages/second throughput
- Dashboard refresh: 4 Hz (250ms)

## Contributing Tests

When adding new features:

1. **Write functional tests first** (TDD with NO MOCKS)
2. Add integration tests for subsystem interactions
3. Add unit tests for pure functions
4. Run full test suite before committing
5. Ensure coverage targets met

## Troubleshooting

### "SDK not available" errors
```bash
# Install Claude Agent SDK
pip install claude-agent-sdk

# Set framework path
export SHANNON_FRAMEWORK_PATH=/path/to/shannon-framework
```

### "Serena MCP not available" errors
```bash
# Install Serena MCP via Claude Code
claude mcp add serena
```

### Timeout errors
```bash
# Increase timeout for slow machines
pytest --timeout=600
```

### Permission errors
```bash
# Ensure temp directories writable
chmod 755 /tmp
```

## Additional Resources

- **Architecture Document**: `docs/SHANNON_CLI_V3_ARCHITECTURE.md`
- **NO MOCKS Philosophy**: Shannon Framework documentation
- **Pytest Documentation**: https://docs.pytest.org
- **Coverage.py**: https://coverage.readthedocs.io

---

**Questions?** See architecture document Section 6 (Testing Architecture)
