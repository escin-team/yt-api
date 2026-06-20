"""Unit tests for parameter validation edge cases."""

import pytest

from youtube_search.utils.errors import InvalidParameterError, MissingParameterError
from youtube_search.utils.validators import (
    validate_keyword,
    validate_limit,
    validate_sort_by,
)


def test_validate_keyword_requires_value():
    """Verify keyword cannot be None or empty."""
    with pytest.raises(MissingParameterError, match="keyword 為必須參數"):
        validate_keyword(None)

    with pytest.raises(MissingParameterError, match="keyword 為必須參數"):
        validate_keyword("")

    with pytest.raises(MissingParameterError, match="keyword 為必須參數"):
        validate_keyword("   ")


def test_validate_keyword_enforces_min_length():
    """Verify keyword must be at least 1 character."""
    # After stripping, empty string should fail
    with pytest.raises(MissingParameterError):
        validate_keyword("  ")


def test_validate_keyword_enforces_max_length():
    """Verify keyword cannot exceed 200 characters."""
    with pytest.raises(InvalidParameterError, match="keyword 長度必須介於 1-200 字元"):
        validate_keyword("x" * 201)


def test_validate_keyword_strips_whitespace():
    """Verify keyword is trimmed."""
    result = validate_keyword("  Python  ")
    assert result == "Python"


def test_validate_limit_defaults_to_1():
    """Verify limit defaults to 1 when None."""
    assert validate_limit(None) == 1


def test_validate_limit_enforces_min():
    """Verify limit must be at least 1."""
    with pytest.raises(InvalidParameterError, match="limit 必須在 1-100 之間"):
        validate_limit(0)

    with pytest.raises(InvalidParameterError, match="limit 必須在 1-100 之間"):
        validate_limit(-5)


def test_validate_limit_enforces_max():
    """Verify limit cannot exceed 100."""
    with pytest.raises(InvalidParameterError, match="limit 必須在 1-100 之間"):
        validate_limit(101)

    with pytest.raises(InvalidParameterError, match="limit 必須在 1-100 之間"):
        validate_limit(200)


def test_validate_limit_allows_valid_range():
    """Verify limit accepts 1-100."""
    assert validate_limit(1) == 1
    assert validate_limit(50) == 50
    assert validate_limit(100) == 100


def test_validate_sort_by_defaults_to_relevance():
    """Verify sort_by defaults to relevance when None."""
    assert validate_sort_by(None) == "relevance"


def test_validate_sort_by_accepts_valid_values():
    """Verify sort_by accepts relevance and date."""
    assert validate_sort_by("relevance") == "relevance"
    assert validate_sort_by("date") == "date"
    assert validate_sort_by("RELEVANCE") == "relevance"  # case insensitive
    assert validate_sort_by("  date  ") == "date"  # strips whitespace


def test_validate_sort_by_rejects_invalid_values():
    """Verify sort_by rejects unsupported values."""
    with pytest.raises(InvalidParameterError, match="sort_by 僅支援 relevance 或 date"):
        validate_sort_by("views")

    with pytest.raises(InvalidParameterError, match="sort_by 僅支援 relevance 或 date"):
        validate_sort_by("popularity")
