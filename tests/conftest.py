"""pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest


# Add project root and src directory to Python path at module level
# This is necessary for import resolution in tests
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

# Only add if not already present to avoid duplicates
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session", autouse=True)
def setup_python_path():
    """
    Provide cleanup for sys.path modifications after all tests complete.
    
    This fixture is auto-used for all tests to ensure proper cleanup.
    The paths are already added at module level (lines 15-18), so this
    fixture only needs to restore the original state for test isolation.
    """
    original_path = sys.path.copy()
    
    yield
    
    # Restore original path after all tests
    sys.path[:] = original_path
