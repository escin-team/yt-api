"""Audio downloader dengan SSL workaround menggunakan impersonate browser."""

import os
import logging
import subprocess
import tempfile
from typing import Optional
from youtube_search.models.download import AudioFile
from youtube_search.services.cloudinary_service import CloudinaryService
from youtube_search.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioDownloader:
    """Download audio dari YouTube dengan impersonate browser untuk bypass SSL."""
    
    def __init__(self):
        self.cloudinary = CloudinaryService()
    
    def _get_ydl_opts(self, output_file: str, timeout: int, bitrate: int, client: str = "web_creator") -> dict:
        """Get yt-dlp options dengan SSL workaround + impersonate."""
        opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'outtmpl': output_file,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'socket_timeout': timeout,
            'retries': 3,
            'fragment_retries': 3,
            'retry_sleep_functions': {
                'http': lambda n: 2 ** n,
                'fragment': lambda n: 2 ** n,
            },
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'nocheckcertificate': True,
            'legacy-server-connect': True,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'force-ipv4': True,
            'no_color': True,
            
            'extractor_args': {
                'youtube': {
                    'player_client': [client],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Platform': '"Windows"',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(bitrate),
            }],
        }
        
        # Cookies — prefer YOUTUBE_COOKIES_FILE path, fall back to YOUTUBE_COOKIES content
        cookies_file = os.getenv('YOUTUBE_COOKIES_FILE')
        if cookies_file and os.path.exists(cookies_file):
            opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies from file: {cookies_file}")
        else:
            cookies_content = os.getenv('YOUTUBE_COOKIES', '').strip()
            if cookies_content:
                cookie_path = '/tmp/youtube_cookies.txt'
                with open(cookie_path, 'w') as f:
                    f.write(cookies_content)
                opts['cookiefile'] = cookie_path
                logger.info("Using cookies from YOUTUBE_COOKIES env var")

        return opts
    
    async def download_and_upload(
        self,
        video_id: str,
        timeout: int = 300,
        max_duration: int = 600,
        bitrate: int = 128
    ) -> AudioFile:
        """Download YouTube video sebagai MP3 dan upload ke Cloudinary."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, f"{video_id}.%(ext)s")
                final_mp3 = os.path.join(temp_dir, f"{video_id}.mp3")
                
                logger.info(f"Downloading video: {video_id}")
                
                import yt_dlp
                
                # Daftar client untuk fallback (tv_embedded & android bypass bot detection best)
                clients = ['tv_embedded', 'android', 'ios', 'web_creator', 'web']
                max_attempts = len(clients)
                last_error = None
                info = None
                
                for attempt_idx, client in enumerate(clients[:max_attempts]):
                    try:
                        logger.info(f"Download attempt {attempt_idx + 1}/{max_attempts} with client: {client}")
                        
                        ydl_opts = self._get_ydl_opts(output_file, timeout, bitrate, client)
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            # Extract info
                            info = ydl.extract_info(
                                f"https://www.youtube.com/watch?v={video_id}",
                                download=False
                            )
                            
                            # Validate duration
                            duration = info.get('duration', 0) or 0
                            if duration > max_duration:
                                raise ValueError(f"Video terlalu panjang ({duration}s > {max_duration}s)")
                            
                            # Download
                            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                        
                        logger.info(f"✅ Download success with client: {client}")
                        break  # Success, exit loop
                        
                    except Exception as e:
                        last_error = e
                        error_str = str(e)
                        logger.warning(f"Attempt {attempt_idx + 1} with {client} failed: {error_str[:200]}")
                        
                        if attempt_idx < max_attempts - 1:
                            import asyncio
                            await asyncio.sleep(2 ** attempt_idx)
                        else:
                            raise
                
                # Cari file yang sudah di-download
                downloaded_file = None
                for ext in ['mp3', 'm4a', 'webm', 'opus']:
                    test_file = os.path.join(temp_dir, f"{video_id}.{ext}")
                    if os.path.exists(test_file):
                        downloaded_file = test_file
                        break
                
                if not downloaded_file:
                    files = os.listdir(temp_dir)
                    raise FileNotFoundError(f"Downloaded file not found. Files: {files}")
                
                # Convert ke MP3 jika perlu
                if not downloaded_file.endswith('.mp3'):
                    logger.info(f"Converting to MP3: {video_id}")
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', downloaded_file,
                        '-vn',
                        '-acodec', 'libmp3lame',
                        '-ab', f'{bitrate}k',
                        '-ar', '44100',
                        '-ac', '2',
                        final_mp3
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=timeout, check=True)
                    downloaded_file = final_mp3
                
                # Upload ke Cloudinary
                logger.info(f"Uploading to Cloudinary: {video_id}")
                cloudinary_url, account_name = await self.cloudinary.upload_file(
                    file_path=downloaded_file,
                    public_id=video_id,
                    folder="music"
                )
                
                audio_file = AudioFile(
                    video_id=video_id,
                    title=info.get('title', 'Unknown'),
                    download_url=cloudinary_url,
                    file_size=os.path.getsize(downloaded_file),
                    duration=info.get('duration', 0) or 0,
                    bitrate=bitrate,
                    storage_account=account_name
                )
                
                logger.info(f"✅ Successfully processed: {video_id}")
                return audio_file
                
        except subprocess.TimeoutExpired:
            raise ValueError(f"FFmpeg timeout setelah {timeout} detik")
        except Exception as e:
            logger.error(f"Failed to process {video_id}: {str(e)}")
            raise