# DSLighting Test Suite

## Overview

This directory contains the complete test suite for DSLighting, including unit tests, integration tests, and fixtures.

## Test Structure

```
tests/
├── README.md                          # This file - Test status tracking
├── conftest.py                        # Pytest configuration and fixtures
├── fixtures/                          # Test data and mock objects
│   ├── sample_data/                   # Sample datasets for testing
│   └── mock_configs/                  # Mock configuration files
├── unit/                              # Unit tests (fast, isolated)
│   ├── test_agent_init.py            # Agent initialization tests
│   ├── test_config_builder.py        # Configuration builder tests
│   ├── test_api_key_rotation.py     # API key rotation tests
│   ├── test_data_loader.py           # Data loader tests
│   └── test_package_detector.py      # Package detection tests
└── integration/                       # Integration tests (slower, may require external deps)
    ├── test_workflows.py             # End-to-end workflow tests
    └── test_grading.py               # MLE-Bench grading tests
```

## Test Status

### ✅ Completed Tests (Unit Tests)

| Test File | Status | Coverage | Last Run | Notes |
|-----------|--------|----------|----------|-------|
| `test_agent_init.py` | ✅ PASS | Agent initialization, workflows, params | 2026-01-18 | All tests passing |
| `test_config_builder.py` | ✅ PASS (14/14) | Configuration system, env vars, JSON parsing, workflow params | 2026-01-18 | All tests passing |

### ⏸️ In Progress Tests

| Test File | Status | Coverage | Last Run | Issues |
|-----------|--------|----------|----------|--------|
| `test_api_key_rotation.py` | ⏸️ 18/19 passing | API key rotation, thread safety | 2026-01-18 | 1 slow test (thread safety) |
| `test_data_loader.py` | ⏸️ Ready | Data loading, task detection | 2026-01-18 | Ready to run full suite |
| `test_package_detector.py` | ⏸️ Ready | Package detection, formatting | - | Ready to test |

### 📝 TODO Tests

#### Unit Tests (Priority: MEDIUM)

- [x] **test_config_builder.py** - Configuration system tests ✅ COMPLETED
  - [x] Test default configuration loading
  - [x] Test environment variable loading
  - [x] Test `LLM_MODEL_CONFIGS` parsing (JSON format)
  - [x] Test configuration priority (code > env > default)
  - [x] Test `api_keys` vs `api_key` field handling
  - [x] Test workflow-specific parameter merging (nested dict format)
  - [x] Test GlobalConfig singleton
  - [x] Test sandbox timeout configuration
  - [x] Test deep merge functionality

- [ ] **test_api_key_rotation.py** - API key rotation tests (v1.9.11+) ⏸️ IN PROGRESS
  - [x] Test `LLMConfig.get_api_keys()` method
  - [x] Test single API key (backward compatibility)
  - [x] Test multiple API keys list
  - [x] Test priority: `api_keys` > `api_key` > `[]`
  - [x] Test `APIKeyManager` round-robin rotation
  - [ ] Test API key rotation on rate limit errors (integration test)
  - [x] Test thread-safe key rotation (slow, passes but takes time)

- [ ] **test_data_loader.py** - Data loading tests ⏸️ READY TO RUN
  - [ ] Run full test suite (24 tests total)
  - [ ] Test `load_data()` with different data types
  - [ ] Test auto-detection of task type (Kaggle vs MLE-Bench)
  - [ ] Test task_id extraction from path
  - [ ] Test DataFrame/dict loading
  - [ ] Test LoadedData object structure
  - [ ] Test CSV/JSON file loading

- [ ] **test_package_detector.py** - Package detection tests ⏸️ READY TO RUN
  - [ ] Run full test suite (16 tests total)
  - [ ] Test package list generation
  - [ ] Test package formatting for LLM context
  - [ ] Test data science package detection
  - [ ] Test exclusion of internal packages
  - [ ] Test version parsing and sorting

#### Integration Tests (Priority: MEDIUM)

- [ ] **test_workflows.py** - End-to-end workflow tests
  - [ ] Test AIDE workflow (simple Kaggle task)
  - [ ] Test AutoKaggle workflow (complex task)
  - [ ] Test DataInterpreter workflow (analysis task)
  - [ ] Test AutoMind workflow with RAG disabled
  - [ ] Test DS-Agent workflow with experience replay
  - [ ] Test DeepAnalyze workflow
  - [ ] **NOTE**: Mark these with `@pytest.mark.requires_llm` as they may cost money

- [ ] **test_grading.py** - MLE-Bench grading tests
  - [ ] Test submission grading
  - [ ] Test score calculation
  - [ ] Test error handling for invalid submissions
  - [ ] Test different grading metrics (RMSE, accuracy, etc.)

### 🚫 Skipping Tests (Not Required)

- [ ] LLM API calls in unit tests (use mocks)
- [ ] External service dependencies (use mocks)
- [ ] Long-running training tasks (> 1 minute)

## Running Tests

### Run All Tests

```bash
# Run all tests
cd /Users/liufan/Applications/Github/dslighting
pytest tests/

# Run with coverage
pytest tests/ --cov=dslighting --cov=dsat --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests (fast)
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Skip tests that require LLM API calls
pytest tests/ -m "not requires_llm"

# Skip slow tests
pytest tests/ -m "not slow"
```

### Run Specific Test Files

```bash
# Test agent initialization
pytest tests/unit/test_agent_init.py -v

# Test API key rotation
pytest tests/unit/test_api_key_rotation.py -v

# Test configuration
pytest tests/unit/test_config_builder.py -v
```

### Run Specific Test Cases

```bash
# Run a specific test
pytest tests/unit/test_agent_init.py::test_agent_init_default -v

# Run tests matching a pattern
pytest tests/unit/ -k "api_key" -v
```

## Test Markers

Pytest markers are used to categorize tests:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_llm` - Tests that require actual LLM API calls (may cost money)
- `@pytest.mark.requires_data` - Tests that require dataset files

## Writing New Tests

### Unit Test Template

```python
"""
Test <feature name>

These tests verify that <feature> works correctly.
"""

import pytest
from dslighting import Agent


@pytest.mark.unit
def test_<feature>_<scenario>():
    """Test that <feature> does <something>"""
    # Arrange
    # Act
    # Assert
    assert True
```

### Integration Test Template

```python
"""
Integration tests for <feature>

These tests verify end-to-end functionality.
"""

import pytest
from dslighting import Agent, load_data


@pytest.mark.integration
@pytest.mark.requires_llm
def test_<feature>_end_to_end():
    """Test <feature> with actual LLM calls"""
    agent = Agent(workflow="aide")
    data = load_data("bike-sharing-demand")
    result = agent.run(data)

    assert result.success
    assert result.score is not None
```

## Fixtures

### Sample Data

Located in `tests/fixtures/sample_data/`:
- `bike-sharing-demand/train.csv` - Training data sample
- `bike-sharing-demand/test.csv` - Test data sample

### Mock Configs

Located in `tests/fixtures/mock_configs/`:
- `default_config.yaml` - Default DSATConfig
- `multi_key_config.yaml` - Multiple API keys configuration

## CI/CD Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request
- Before releases

## Coverage Goals

Target coverage:
- Unit tests: > 80%
- Integration tests: > 60%
- Overall: > 70%

Current coverage: [TO BE UPDATED]

## Troubleshooting

### Tests Fail with "No API Key"

Set up your environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Tests Fail with "Module Not Found"

Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Integration Tests Timeout

Increase timeout in `conftest.py` or skip slow tests:
```bash
pytest tests/ -m "not slow"
```

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Ensure all tests pass before pushing
3. Update this README with test status
4. Add fixtures if needed

---

**Last Updated:** 2026-01-18
**Test Suite Version:** v1.9.12
**Maintainer:** DSLighting Team
