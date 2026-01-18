"""
pytest configuration and fixtures for DSLighting tests
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
import pandas as pd


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Path:
    """
    Create a temporary directory for testing.

    Yields:
        Path: Temporary directory path (auto-cleaned after test)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_data_dir(temp_dir: Path) -> Path:
    """
    Create a sample data directory with test files.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Path to sample data directory
    """
    data_dir = temp_dir / "test_data"
    data_dir.mkdir()

    # Create sample CSV files
    train_df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [10, 20, 30, 40, 50],
        'target': [0, 1, 0, 1, 0]
    })
    train_df.to_csv(data_dir / "train.csv", index=False)

    test_df = pd.DataFrame({
        'feature1': [6, 7, 8],
        'feature2': [60, 70, 80]
    })
    test_df.to_csv(data_dir / "test.csv", index=False)

    return data_dir


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """
    Create a sample DataFrame for testing.

    Returns:
        pd.DataFrame: Sample dataframe with test data
    """
    return pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10],
        'category': ['A', 'B', 'A', 'B', 'A']
    })


@pytest.fixture
def sample_classification_data() -> Dict[str, Any]:
    """
    Create sample classification task data.

    Returns:
        Dict with train and test DataFrames
    """
    train_df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [10, 20, 30, 40, 50],
        'target': [0, 1, 0, 1, 0]
    })

    test_df = pd.DataFrame({
        'feature1': [6, 7, 8],
        'feature2': [60, 70, 80]
    })

    return {
        'train': train_df,
        'test': test_df,
        'target': 'target',
        'task_type': 'classification'
    }


# ============================================================================
# LLM Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """
    Create a mock LLM API response.

    Returns:
        Dict: Mock LLM response structure
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a test response from the LLM."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_llm_stream_response() -> Dict[str, Any]:
    """
    Create a mock LLM streaming response.

    Returns:
        Dict: Mock streaming response structure
    """
    return {
        "id": "chatcmpl-test456",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "delta": {
                "content": "Test"
            },
            "finish_reason": None
        }]
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def basic_agent_config() -> Dict[str, Any]:
    """
    Create basic agent configuration.

    Returns:
        Dict: Basic agent configuration
    """
    return {
        "workflow": "aide",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_iterations": 5
    }


@pytest.fixture
def aide_config() -> Dict[str, Any]:
    """
    Create AIDE workflow configuration.

    Returns:
        Dict: AIDE-specific configuration
    """
    return {
        "workflow": "aide",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_iterations": 10
    }


@pytest.fixture
def dsagent_config_with_rag_disabled() -> Dict[str, Any]:
    """
    Create DS-Agent configuration with RAG disabled.

    Returns:
        Dict: DS-Agent configuration without RAG
    """
    return {
        "workflow": "dsagent",
        "model": "gpt-4o",
        "temperature": 0.6,
        "max_iterations": 15,
        "dsagent": {
            "enable_rag": False,
            "case_dir": "./experience_replay"
        }
    }


@pytest.fixture
def automind_config_with_rag_disabled() -> Dict[str, Any]:
    """
    Create AutoMind configuration with RAG disabled.

    Returns:
        Dict: AutoMind configuration without RAG
    """
    return {
        "workflow": "automind",
        "model": "gpt-4o",
        "temperature": 0.5,
        "max_iterations": 10,
        "automind": {
            "enable_rag": False,
            "case_dir": "./experience_replay"
        }
    }


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(autouse=True)
def reset_global_config():
    """
    Reset global configuration before each test.

    This fixture runs automatically for every test to ensure
    test isolation.
    """
    # Reset global config before test
    import dslighting.core.global_config as gc
    original_config = gc.GLOBAL_CONFIG.copy()
    gc.GLOBAL_CONFIG.clear()

    yield

    # Restore after test
    gc.GLOBAL_CONFIG.update(original_config)


# ============================================================================
# Performance Markers
# ============================================================================

def pytest_configure(config):
    """
    Configure custom pytest markers.

    Args:
        config: pytest config object
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, may require external dependencies)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (skip with -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "requires_llm: Tests that require actual LLM API calls (may cost money)"
    )
    config.addinivalue_line(
        "markers", "requires_data: Tests that require dataset files"
    )
