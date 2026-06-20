"""YouTube scraper dengan SSL workaround dan Invidious fallback."""

import asyncio
import logging
import random
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache
import httpx
from youtube_search.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# User agents modern untuk bypass detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Invidious instances sebagai fallback (cek status di https://api.invidious.io/)
INVIDIOUS_INSTANCES = [
    "https://vid.puffyan.us",
    "https://invidious.fdn.fr",
    "https://inv.tux.pizza",
    "https://invidious.perennialte.ch",
    "https://iv.ggtyler.dev",
    "https://invidious.privacyredirect.com",
    "https://invidious.lunar.icu",
    "https://yt.drgnz.club",
]


class YouTubeScraper:
    """Scraper YouTube dengan SSL workaround dan multi-fallback."""
    
    def __init__(self):
        self.client = None
        self.settings = get_settings()
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                max(self.settings.youtube_timeout, 30) * 2,
                connect=15.0
            ),
            follow_redirects=True,
            verify=False,  # ⭐ Disable SSL verification untuk cloud environments
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Mode": "navigate",
            },
            http2=True  # ⭐ Force HTTP/2
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def search(self, keyword: str, limit: int = 20, sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        Search YouTube videos dengan fallback multi-layer.
        
        Priority:
        1. Invidious API (paling reliable di cloud)
        2. youtube-search package (fallback library)
        3. YouTube direct (paling sering diblok di cloud)
        
        Args:
            keyword: Search query
            limit: Max results
            sort_by: "relevance" or "date"
        
        Returns:
            List of video dicts
        """
        # Priority 1: Invidious (paling reliable di cloud)
        try:
            results = await self._search_invidious(keyword, limit, sort_by)
            if results:
                logger.info(f"✅ Invidious search success: {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"Invidious search failed: {e}")
        
        # Priority 2: youtube-search package
        try:
            results = await self._search_fallback_package(keyword, limit)
            if results:
                logger.info(f"✅ Fallback package search success: {len(results)} results")
                return results
        except Exception as e:
            logger.warning(f"Fallback package search failed: {e}")
        
        # Priority 3: YouTube direct (last resort)
        try:
            results = await self._search_youtube_direct(keyword, limit, sort_by)
            if results:
                logger.info(f"✅ YouTube direct search success: {len(results)} results")
                return results
        except Exception as e:
            logger.error(f"YouTube direct search also failed: {e}")
        
        logger.error(f"❌ All search methods failed for keyword: {keyword}")
        return []
    
    async def _search_youtube_direct(self, keyword: str, limit: int, sort_by: str) -> List[Dict[str, Any]]:
        """Search langsung ke YouTube (sering diblok di cloud)."""
        search_url = f"{self.settings.youtube_base_url}?search_query={keyword}"
        
        if sort_by == "date":
            search_url += "&sp=CAI%253D"  # Sort by upload date
        
        try:
            response = await self.client.get(search_url)
            response.raise_for_status()
            
            # Parse HTML YouTube (simplified - implementasi lengkap di file asli)
            html = response.text
            
            # Extract video data dari ytInitialData
            videos = []
            pattern = r'"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"'
            matches = re.findall(pattern, html)
            
            for video_id, title in matches[:limit]:
                videos.append({
                    "video_id": video_id,
                    "title": title.encode().decode('unicode_escape'),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": None,
                    "channel_url": None,
                    "publish_date": None,
                    "view_count": 0,
                    "description": "",
                    "duration": None,
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"YouTube direct search error: {e}")
            raise
    
    async def _search_invidious(self, keyword: str, limit: int, sort_by: str) -> List[Dict[str, Any]]:
        """Search via Invidious API (paling reliable di cloud)."""
        
        sort_param = {
            "relevance": "relevance",
            "date": "upload_date",
            "views": "view_count",
            "rating": "rating",
        }.get(sort_by, "relevance")
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                api_url = f"{instance}/api/v1/search"
                params = {
                    "q": keyword,
                    "sort_by": sort_param,
                    "type": "video",
                    "page": 1,
                }
                
                response = await self.client.get(api_url, params=params, timeout=15.0)
                response.raise_for_status()
                
                data = response.json()
                videos = []
                
                for item in data:
                    if item.get("type") == "video" and len(videos) < limit:
                        # Get best thumbnail
                        thumbnails = item.get("videoThumbnails", [])
                        thumbnail_url = None
                        for thumb in thumbnails:
                            if thumb.get("quality") in ["medium", "high"]:
                                thumbnail_url = thumb.get("url")
                                break
                        if not thumbnail_url and thumbnails:
                            thumbnail_url = thumbnails[0].get("url")
                        
                        videos.append({
                            "video_id": item.get("videoId"),
                            "title": item.get("title"),
                            "url": f"https://www.youtube.com/watch?v={item.get('videoId')}",
                            "channel": item.get("author"),
                            "channel_url": item.get("authorUrl"),
                            "publish_date": item.get("publishedText"),
                            "view_count": item.get("viewCount", 0) or 0,
                            "description": (item.get("description") or "")[:200],
                            "duration": item.get("lengthSeconds"),
                            "thumbnail": thumbnail_url,
                        })
                
                if videos:
                    return videos
                    
            except Exception as e:
                logger.warning(f"Invidious instance {instance} failed: {e}")
                continue
        
        return []
    
    async def _search_fallback_package(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Search pakai youtube-search package (ultimate fallback)."""
        try:
            from youtube_search import YoutubeSearch
            
            def sync_search():
                searcher = YoutubeSearch(keyword, max_results=limit)
                return searcher.results()
            
            # Run in thread pool untuk blocking call
            results = await asyncio.to_thread(sync_search)
            
            videos = []
            for item in results:
                video_id = item.get("id")
                url_suffix = item.get("url_suffix", "")
                
                videos.append({
                    "video_id": video_id,
                    "title": item.get("title"),
                    "url": f"https://www.youtube.com{url_suffix}",
                    "channel": item.get("channel"),
                    "channel_url": None,
                    "publish_date": item.get("publish_time"),
                    "view_count": self._parse_view_count(item.get("views", "0")),
                    "description": (item.get("long_desc") or "")[:200],
                    "duration": self._parse_duration(item.get("duration", "0:00")),
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Fallback package failed: {e}")
            return []
    
    def _parse_view_count(self, views_str: str) -> int:
        """Parse view count string like '1,234,567 views' to int."""
        try:
            match = re.search(r'[\d,]+', str(views_str).replace(',', ''))
            return int(match.group()) if match else 0
        except:
            return 0
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '3:45' to seconds."""
        try:
            parts = str(duration_str).split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except:
            return 0


# ============================================
# SINGLETON & HELPER FUNCTIONS
# ============================================

_scraper_instance: Optional[YouTubeScraper] = None


def get_scraper() -> YouTubeScraper:
    """
    Get singleton instance of YouTubeScraper.
    
    Returns:
        YouTubeScraper instance
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = YouTubeScraper()
    return _scraper_instance


async def search_youtube(keyword: str, limit: int = 20, sort_by: str = "relevance") -> List[Dict[str, Any]]:
    """
    Public function untuk search YouTube.
    
    Args:
        keyword: Search query
        limit: Max results
        sort_by: "relevance" or "date"
    
    Returns:
        List of video dicts
    """
    async with get_scraper() as scraper:
        return await scraper.search(keyword, limit, sort_by)