"""Integration tests for API metadata responses."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from youtube_search.models.search import SearchResult
from youtube_search.models.video import Video
from youtube_search.services.search import SearchService, get_search_service


class FakeMetadataService(SearchService):
    async def search(
        self, keyword: str, limit: int = 1, sort_by: str = "relevance"
    ) -> SearchResult:
        video = Video(
            video_id="test12345id",
            title="Python 教學影片",
            url=Video.build_url("test12345id"),
            channel="教學頻道",
            channel_url="https://www.youtube.com/c/example",
            publish_date="2024-01-15T10:30:00Z",
            view_count=50000,
            description="從入門到精通的 Python 教學",
        )
        return SearchResult(search_keyword=keyword, videos=[video], result_count=1)


def setup_module(_module):
    app.dependency_overrides[get_search_service] = lambda: FakeMetadataService()


def teardown_module(_module):
    app.dependency_overrides.clear()


def test_api_returns_full_metadata():
    """Verify API response includes all metadata fields."""
    client = TestClient(app)
    response = client.get("/api/v1/search", params={"keyword": "Python", "limit": 1})
    assert response.status_code == 200

    data = response.json()
    video = data["videos"][0]
    assert video["video_id"] == "test12345id"
    assert video["title"] == "Python 教學影片"
    assert video["channel"] == "教學頻道"
    assert video["channel_url"] == "https://www.youtube.com/c/example"
    assert video["publish_date"] == "2024-01-15T10:30:00Z"
    assert video["view_count"] == 50000
    assert video["description"] == "從入門到精通的 Python 教學"


def test_api_handles_null_metadata_fields():
    """Verify API correctly serializes null fields."""

    class PartialMetadataService(SearchService):
        async def search(
            self, keyword: str, limit: int = 1, sort_by: str = "relevance"
        ) -> SearchResult:
            video = Video(
                video_id="partial1234",
                title="Partial Video",
                url=Video.build_url("partial1234"),
                channel=None,
                channel_url=None,
                publish_date=None,
                view_count=None,
                description=None,
            )
            return SearchResult(search_keyword=keyword, videos=[video], result_count=1)

    app.dependency_overrides[get_search_service] = lambda: PartialMetadataService()

    client = TestClient(app)
    response = client.get("/api/v1/search", params={"keyword": "test"})
    assert response.status_code == 200

    # With response_model_exclude_none=True, null fields should be excluded
    data = response.json()
    video = data["videos"][0]
    assert "channel" not in video or video["channel"] is None
    assert "view_count" not in video or video["view_count"] is None
