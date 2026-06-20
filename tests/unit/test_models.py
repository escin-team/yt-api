"""Unit tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from youtube_search.models.search import SearchResult
from youtube_search.models.video import Video


def test_video_requires_video_id():
    """Verify Video model enforces video_id presence."""
    with pytest.raises(ValidationError, match="video_id"):
        Video()


def test_video_validates_video_id_format():
    """Verify Video model enforces 11-character alphanumeric pattern."""
    with pytest.raises(ValidationError):
        Video(video_id="invalid")

    # Valid format should pass
    video = Video(video_id="abc12345678")
    assert video.video_id == "abc12345678"


def test_video_allows_null_optional_fields():
    """Verify optional fields can be None."""
    video = Video(
        video_id="test1234567",
        title=None,
        channel=None,
        publish_date=None,
        view_count=None,
    )
    assert video.title is None
    assert video.channel is None


def test_video_validates_publish_date_iso8601():
    """Verify publish_date must be valid ISO 8601 format."""
    with pytest.raises(ValidationError, match="ISO 8601"):
        Video(video_id="test1234567", publish_date="not a date")

    # Valid ISO 8601 should pass
    video = Video(video_id="test1234567", publish_date="2024-01-15T10:30:00Z")
    assert video.publish_date == "2024-01-15T10:30:00Z"


def test_video_validates_view_count_non_negative():
    """Verify view_count must be non-negative."""
    with pytest.raises(ValidationError):
        Video(video_id="test1234567", view_count=-100)

    # Non-negative should pass
    video = Video(video_id="test1234567", view_count=0)
    assert video.view_count == 0


def test_video_enforces_title_max_length():
    """Verify title max length constraint."""
    with pytest.raises(ValidationError):
        Video(video_id="test1234567", title="x" * 501)

    # Within limit should pass
    video = Video(video_id="test1234567", title="x" * 500)
    assert len(video.title) == 500


def test_search_result_validates_result_count_matches_videos():
    """Verify result_count must equal videos array length."""
    with pytest.raises(ValidationError, match="result_count"):
        SearchResult(
            search_keyword="test",
            result_count=5,
            videos=[Video(video_id="test1234567")],
        )

    # Matching count should pass
    result = SearchResult(
        search_keyword="test", result_count=1, videos=[Video(video_id="test1234567")]
    )
    assert result.result_count == 1


def test_search_result_requires_keyword():
    """Verify search_keyword is required."""
    with pytest.raises(ValidationError, match="search_keyword"):
        SearchResult(result_count=0, videos=[])


def test_search_result_validates_keyword_length():
    """Verify search_keyword length constraints."""
    with pytest.raises(ValidationError):
        SearchResult(search_keyword="", result_count=0, videos=[])

    with pytest.raises(ValidationError):
        SearchResult(search_keyword="x" * 201, result_count=0, videos=[])

    # Valid length should pass
    result = SearchResult(search_keyword="Python", result_count=0, videos=[])
    assert result.search_keyword == "Python"


def test_search_result_generates_timestamp():
    """Verify SearchResult auto-generates timestamp."""
    result = SearchResult(search_keyword="test", result_count=0, videos=[])
    assert result.timestamp is not None
    assert "T" in result.timestamp
    assert result.timestamp.endswith("Z")
