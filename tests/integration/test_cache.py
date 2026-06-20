"""Integration tests for Redis caching."""

from unittest.mock import MagicMock

from youtube_search.models.playlist import Playlist, Track
from youtube_search.models.search import SearchResult
from youtube_search.models.video import Video
from youtube_search.services.cache import CacheService


def test_cache_get_returns_none_when_disabled():
    """Verify cache gracefully returns None when Redis disabled."""
    cache = CacheService(redis_client=None)
    result = cache.get("test")
    assert result is None


def test_cache_set_does_nothing_when_disabled():
    """Verify cache.set doesn't crash when Redis disabled."""
    cache = CacheService(redis_client=None)
    result = SearchResult(search_keyword="test", videos=[], result_count=0)
    cache.set("test", result)  # Should not raise


def test_cache_roundtrip_with_mock_redis():
    """Verify cache can store and retrieve SearchResult."""
    mock_redis = MagicMock()
    cache = CacheService(redis_client=mock_redis)

    video = Video(video_id="test1234567", title="Test Video")
    result = SearchResult(search_keyword="Python", videos=[video], result_count=1)

    # Mock setex to store data
    stored_data = {}

    def mock_setex(key, ttl, value):
        stored_data[key] = value

    def mock_get(key):
        return stored_data.get(key)

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get

    cache.set("Python", result)
    cached = cache.get("Python")

    assert cached is not None
    assert cached.search_keyword == "Python"
    assert cached.result_count == 1
    assert cached.videos[0].video_id == "test1234567"


def test_playlist_cache_hit_with_mock_redis():
    """Verify playlist cache hit on second request (T023 smoke test)."""
    mock_redis = MagicMock()
    cache = CacheService(redis_client=mock_redis)

    # Create a playlist with tracks
    track = Track(
        video_id="dQw4w9WgXcQ",
        title="Never Gonna Give You Up",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    playlist = Playlist(
        playlist_id="PLtest1234567",
        url="https://www.youtube.com/playlist?list=PLtest1234567",
        title="Test Playlist",
        video_count=1,
        partial=False,
        tracks=[track],
    )

    stored_data = {}

    def mock_setex(key, ttl, value):
        stored_data[key] = value

    def mock_get(key):
        return stored_data.get(key)

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get

    # First request should miss cache
    cache.set("playlist:PLtest1234567", playlist)

    # Second request should hit cache
    cached = cache.get("playlist:PLtest1234567", model_class=Playlist)
    assert cached is not None
    assert cached.playlist_id == "PLtest1234567"
    assert len(cached.tracks) == 1
    assert cached.tracks[0].title == "Never Gonna Give You Up"


def test_cache_disabled_returns_none_for_partial_playlist():
    """Verify cache returns None when Redis is disabled (even for partial playlists).
    
    Note: The actual logic to skip caching partial playlists is implemented in
    PlaylistService.get_playlist_metadata() (lines 100-110), not in the cache service.
    """
    cache = CacheService(redis_client=None)

    partial_playlist = Playlist(
        playlist_id="PLtest9999",
        url="https://www.youtube.com/playlist?list=PLtest9999",
        title="Partial Playlist",
        video_count=1000,
        partial=True,  # Incomplete due to timeout
        tracks=[],
    )

    # Attempt to cache partial playlist
    cache.set("playlist:PLtest9999", partial_playlist)

    # Verify cache returns None (Redis is disabled)
    result = cache.get("playlist:PLtest9999")
    assert result is None


def test_cache_key_generation_is_deterministic():
    """Verify cache key is consistent for same keyword."""
    key1 = CacheService._generate_key("Python教學")
    key2 = CacheService._generate_key("Python教學")
    assert key1 == key2
    assert key1.startswith("youtube_search:")


def test_cache_key_generation_differs_for_different_keywords():
    """Verify different keywords generate different cache keys."""
    key1 = CacheService._generate_key("Python")
    key2 = CacheService._generate_key("JavaScript")
    assert key1 != key2
