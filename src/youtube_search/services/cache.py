"""Redis caching layer for search results and playlists."""

from __future__ import annotations

import hashlib
import json
from typing import Optional, Type, TypeVar, Union

import redis
from pydantic import BaseModel

from youtube_search.config import get_settings
from youtube_search.models.search import SearchResult
from youtube_search.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class CacheService:
    """Manage Redis caching for search results."""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        settings = get_settings()
        if redis_client:
            self.client = redis_client
            logger.info("Using provided Redis client")
        elif settings.redis_enabled:
            logger.info(
                "Attempting to connect to Redis",
                extra={
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "db": settings.redis_db,
                    "has_password": bool(settings.redis_password),
                },
            )
            try:
                self.client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # Test connection
                self.client.ping()
                logger.info(
                    "Redis connection established successfully",
                    extra={
                        "host": settings.redis_host,
                        "port": settings.redis_port,
                        "db": settings.redis_db,
                        "status": "connected",
                    },
                )
            except (redis.RedisError, OSError) as exc:  # pragma: no cover
                import socket

                # Try to get more diagnostic information
                diagnostic_info = {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "db": settings.redis_db,
                    "status": "disconnected",
                }

                # Try DNS resolution
                try:
                    resolved_ip = socket.gethostbyname(settings.redis_host)
                    diagnostic_info["resolved_ip"] = resolved_ip
                except socket.gaierror as dns_error:
                    diagnostic_info["dns_error"] = str(dns_error)
                    diagnostic_info["dns_resolution"] = "failed"

                logger.error(
                    "Redis connection failed - running without cache",
                    extra=diagnostic_info,
                )
                self.client = None
        else:
            logger.info("Redis cache is disabled by configuration", extra={"status": "disabled"})
            self.client = None
        self.ttl = settings.redis_ttl_seconds

    def get(
        self, keyword: str, model_class: Optional[Type[T]] = None
    ) -> Optional[Union[SearchResult, T]]:
        """Retrieve cached result for keyword.

        Args:
            keyword: Cache key (e.g. 'python', 'playlist:PLxxxxx')
            model_class: Optional model class to deserialize into. Defaults to SearchResult.

        Returns:
            Deserialized model instance or None if not found/error.
        """

        if not self.client:
            return None

        if model_class is None:
            model_class = SearchResult

        cache_key = self._generate_key(keyword)
        try:
            cached = self.client.get(cache_key)
            if cached:
                logger.debug("Cache hit", extra={"keyword": keyword})
                data = json.loads(cached)
                return model_class(**data)
        except (redis.RedisError, json.JSONDecodeError) as exc:  # pragma: no cover
            logger.warning("Cache retrieval failed", extra={"error": str(exc)})
        return None

    def set(self, keyword: str, result: Union[SearchResult, BaseModel]) -> None:
        """Store result in cache with TTL.

        Args:
            keyword: Cache key (e.g. 'python', 'playlist:PLxxxxx')
            result: Model instance to serialize and cache.
        """

        if not self.client:
            return

        cache_key = self._generate_key(keyword)
        try:
            serialized = result.model_dump_json()
            self.client.setex(cache_key, self.ttl, serialized)
            logger.debug("Cache set", extra={"keyword": keyword, "ttl": self.ttl})
        except redis.RedisError as exc:  # pragma: no cover
            logger.warning("Cache storage failed", extra={"error": str(exc)})

    @staticmethod
    def _generate_key(keyword: str) -> str:
        """Generate SHA256 hash-based cache key."""

        hash_obj = hashlib.sha256(keyword.encode("utf-8"))
        return f"youtube_search:{hash_obj.hexdigest()}"


_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Return singleton cache service instance."""

    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
