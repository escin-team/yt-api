"""Smoke test for GET /api/v1/search."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from youtube_search.models.search import SearchResult
from youtube_search.models.video import Video
from youtube_search.services.search import SearchService, get_search_service


class FakeSearchService(SearchService):
    async def search(
        self, keyword: str, limit: int = 1, sort_by: str = "relevance"
    ) -> SearchResult:
        video = Video(
            video_id="abc123def45", title="sample", url=Video.build_url("abc123def45")
        )
        return SearchResult(search_keyword=keyword, videos=[video], result_count=1)


def setup_module(_module):
    app.dependency_overrides[get_search_service] = lambda: FakeSearchService()


def teardown_module(_module):
    app.dependency_overrides.clear()


def test_search_endpoint_returns_200():
    client = TestClient(app)
    response = client.get("/api/v1/search", params={"keyword": "Python"})
    assert response.status_code == 200
    data = response.json()
    assert data["search_keyword"] == "Python"
    assert data["result_count"] == 1
    assert len(data["videos"]) == 1
    assert data["videos"][0]["video_id"] == "abc123def45"


def test_missing_keyword_returns_400():
    client = TestClient(app)
    response = client.get("/api/v1/search")
    assert response.status_code == 422 or response.status_code == 400
    # FastAPI validation returns 422 when query param missing; our validator returns 400 when provided empty.


def test_invalid_limit_returns_400():
    client = TestClient(app)
    response = client.get("/api/v1/search", params={"keyword": "Python", "limit": 0})
    assert response.status_code == 422 or response.status_code == 400
