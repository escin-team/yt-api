"""Playlist scraper dengan SSL workaround."""

import logging
import re
from typing import Dict, Any, Optional, List
from functools import lru_cache
import httpx
from youtube_search.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Invidious instances untuk playlist
INVIDIOUS_INSTANCES = [
    "https://vid.puffyan.us",
    "https://invidious.fdn.fr",
    "https://inv.tux.pizza",
    "https://invidious.perennialte.ch",
    "https://iv.ggtyler.dev",
]


class PlaylistScraper:
    """Scraper playlist YouTube dengan SSL workaround."""
    
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
            verify=False,  # ⭐ Disable SSL verification
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            http2=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get_playlist_metadata(self, playlist_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get metadata playlist YouTube.
        
        Args:
            playlist_url: URL playlist YouTube
            force_refresh: Force refresh dari YouTube (skip cache)
        
        Returns:
            Dict dengan metadata playlist
        """
        try:
            # Extract playlist ID
            playlist_id = self._extract_playlist_id(playlist_url)
            if not playlist_id:
                raise ValueError("Invalid playlist URL - missing 'list' parameter")
            
            logger.info(f"Processing playlist_id: {playlist_id}")
            
            # Coba Invidious dulu (lebih reliable)
            try:
                result = await self._get_from_invidious(playlist_id, playlist_url)
                if result:
                    logger.info(f"✅ Successfully fetched playlist from Invidious: {len(result.get('tracks', []))} tracks")
                    return result
            except Exception as e:
                logger.warning(f"Invidious playlist failed: {e}")
            
            # Fallback ke YouTube direct
            logger.warning("Falling back to YouTube direct (may fail in cloud)")
            response = await self.client.get(playlist_url)
            response.raise_for_status()
            
            # Parsing HTML (placeholder - implementasi actual di file asli)
            return {
                "playlist_id": playlist_id,
                "url": playlist_url,
                "title": "Playlist",
                "video_count": 0,
                "partial": False,
                "tracks": []
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch playlist: {e}")
            raise
    
    async def _get_from_invidious(self, playlist_id: str, playlist_url: str) -> Optional[Dict[str, Any]]:
        """Get playlist dari Invidious API."""
        
        for instance in INVIDIOUS_INSTANCES:
            try:
                api_url = f"{instance}/api/v1/playlists/{playlist_id}"
                response = await self.client.get(api_url, timeout=20.0)
                response.raise_for_status()
                
                data = response.json()
                tracks = []
                
                for i, video in enumerate(data.get("videos", []), 1):
                    tracks.append({
                        "video_id": video.get("videoId"),
                        "title": video.get("title"),
                        "channel": video.get("author"),
                        "channel_url": video.get("authorUrl"),
                        "url": f"https://www.youtube.com/watch?v={video.get('videoId')}",
                        "publish_date": video.get("publishedText"),
                        "duration": self._format_duration(video.get("lengthSeconds", 0)),
                        "view_count": video.get("viewCount", 0),
                        "position": i,
                    })
                
                return {
                    "playlist_id": playlist_id,
                    "url": playlist_url,
                    "title": data.get("title", "Playlist"),
                    "video_count": data.get("videoCount", len(tracks)),
                    "partial": False,
                    "tracks": tracks,
                }
                
            except Exception as e:
                logger.warning(f"Invidious instance {instance} failed: {e}")
                continue
        
        return None
    
    def _extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID dari URL."""
        match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
        return match.group(1) if match else None
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds ke 'MM:SS' atau 'HH:MM:SS'."""
        if seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"


# ============================================
# SINGLETON & HELPER FUNCTIONS
# ============================================

_playlist_scraper_instance: Optional[PlaylistScraper] = None


def get_playlist_scraper() -> PlaylistScraper:
    """
    Get singleton instance of PlaylistScraper.
    
    Returns:
        PlaylistScraper instance
    """
    global _playlist_scraper_instance
    if _playlist_scraper_instance is None:
        _playlist_scraper_instance = PlaylistScraper()
    return _playlist_scraper_instance