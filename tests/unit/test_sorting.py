"""Unit tests for sorting logic."""

from youtube_search.models.video import Video
from youtube_search.services.sorter import VideoSorter


def test_sort_by_relevance_preserves_order():
    """Verify relevance sorting keeps original order."""
    sorter = VideoSorter()
    videos = [
        Video(video_id="video000001"),
        Video(video_id="video000002"),
        Video(video_id="video000003"),
    ]
    result = sorter.sort(videos, "relevance")
    assert [v.video_id for v in result] == ["video000001", "video000002", "video000003"]


def test_sort_by_date_descending():
    """Verify date sorting places newer videos first."""
    sorter = VideoSorter()
    videos = [
        Video(video_id="old12345678", publish_date="2023-01-01T00:00:00Z"),
        Video(video_id="new12345678", publish_date="2024-06-15T12:00:00Z"),
        Video(video_id="mid12345678", publish_date="2023-12-31T23:59:59Z"),
    ]
    result = sorter.sort(videos, "date")
    assert result[0].video_id == "new12345678"
    assert result[1].video_id == "mid12345678"
    assert result[2].video_id == "old12345678"


def test_sort_by_date_places_null_dates_at_end():
    """Verify videos without publish_date are placed at the end."""
    sorter = VideoSorter()
    videos = [
        Video(video_id="nodate00001", publish_date=None),
        Video(video_id="dated000001", publish_date="2024-01-01T00:00:00Z"),
        Video(video_id="nodate00002", publish_date=None),
    ]
    result = sorter.sort(videos, "date")
    assert result[0].video_id == "dated000001"
    # Remaining two with null dates come after, order among nulls is stable
    assert result[1].video_id in ["nodate00001", "nodate00002"]
    assert result[2].video_id in ["nodate00001", "nodate00002"]


def test_sort_handles_empty_list():
    """Verify sorting empty list returns empty list."""
    sorter = VideoSorter()
    result = sorter.sort([], "relevance")
    assert result == []
    result_date = sorter.sort([], "date")
    assert result_date == []
