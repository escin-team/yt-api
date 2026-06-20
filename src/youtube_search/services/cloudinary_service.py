"""Cloudinary service with multi-account failover support."""

import os
import json
import logging
from typing import Tuple, Optional, List, Dict, Any
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from youtube_search.config import get_settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Cloudinary upload service with automatic failover across multiple accounts."""
    
    def __init__(self):
        self.settings = get_settings()
        self.accounts = self.settings.cloudinary_accounts
        self.current_account_index = 0
        
        if not self.accounts:
            logger.warning(
                "CLOUDINARY_ACCOUNTS_JSON is empty or not set — "
                "files will be served from local storage only."
            )
    
    def _configure_account(self, account: Dict[str, Any]) -> bool:
        """Configure Cloudinary with given account credentials."""
        try:
            cloudinary.config(
                cloud_name=account.get("cloud_name"),
                api_key=account.get("api_key"),
                api_secret=account.get("api_secret"),
                secure=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to configure Cloudinary account {account.get('name', 'unknown')}: {e}")
            return False
    
    async def upload_file(
        self,
        file_path: str,
        public_id: str,
        folder: str = "music",
        resource_type: str = "video"  # Cloudinary treats audio as video
    ) -> Tuple[str, str]:
        """
        Upload file to Cloudinary with automatic failover.
        
        Args:
            file_path: Local path to file
            public_id: Public ID for the file (usually video_id)
            folder: Cloudinary folder name
            resource_type: 'video' for audio files in Cloudinary
        
        Returns:
            Tuple of (download_url, account_name)
        
        Raises:
            RuntimeError: If all accounts fail
        """
        if not self.accounts:
            # Fallback: return local file URL (tidak akan persisten)
            local_url = f"http://localhost:{self.settings.api_port}/local/{public_id}.mp3"
            logger.warning(f"No Cloudinary accounts, returning local URL: {local_url}")
            return local_url, "local"
        
        errors = []
        
        # Try each account in order (failover)
        for account in self.accounts:
            account_name = account.get("name", "unknown")
            
            try:
                logger.info(f"Attempting upload to Cloudinary account: {account_name}")
                
                # Configure account
                if not self._configure_account(account):
                    errors.append(f"{account_name}: configuration failed")
                    continue
                
                # Upload file
                result = cloudinary.uploader.upload(
                    file_path,
                    resource_type=resource_type,
                    folder=folder,
                    public_id=public_id,
                    format="mp3",
                    overwrite=True,
                    invalidate=True
                )
                
                # Get secure URL
                download_url = result.get("secure_url")
                
                if not download_url:
                    raise ValueError("No secure_url in response")
                
                logger.info(
                    f"✅ Upload successful to {account_name}: {download_url}"
                )
                return download_url, account_name
                
            except CloudinaryError as e:
                error_msg = f"{account_name}: {str(e)}"
                logger.warning(f"Cloudinary error on {account_name}: {e}")
                errors.append(error_msg)
                continue
                
            except Exception as e:
                error_msg = f"{account_name}: {str(e)}"
                logger.error(f"Unexpected error on {account_name}: {e}")
                errors.append(error_msg)
                continue
        
        # All accounts failed
        error_summary = " | ".join(errors)
        raise RuntimeError(
            f"All Cloudinary accounts failed. Errors: {error_summary}"
        )
    
    async def delete_file(self, public_id: str, folder: str = "music") -> bool:
        """Delete file from Cloudinary (all accounts)."""
        if not self.accounts:
            return False
        
        success = False
        for account in self.accounts:
            try:
                self._configure_account(account)
                result = cloudinary.uploader.destroy(
                    f"{folder}/{public_id}",
                    resource_type="video"
                )
                if result.get("result") == "ok":
                    success = True
            except Exception as e:
                logger.warning(f"Failed to delete from {account.get('name')}: {e}")
        
        return success
    
    def get_account_count(self) -> int:
        """Get number of configured accounts."""
        return len(self.accounts)