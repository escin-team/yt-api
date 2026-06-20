#!/usr/bin/env python
"""清理腳本 - 可被 cron 執行的下載檔案清理入口點。

使用範例：
    # 手動執行一次
    python scripts/cleanup_cron.py

    # 配置為 cron 任務（每日凌晨 2 點執行）
    0 2 * * * /usr/bin/python /path/to/scripts/cleanup_cron.py >> /path/to/logs/cleanup.log 2>&1
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> logging.Logger:
    """設定清理腳本的日誌。"""
    from youtube_search.utils.logger import get_logger

    logger = get_logger("cleanup_script")

    # 添加檔案處理器用於 cleanup.log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / "cleanup.log",
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [清理] %(message)s [%(filename)s:%(lineno)d]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


async def main() -> int:
    """
    主清理任務。

    Returns:
        int: 退出碼（0 = 成功, 1 = 失敗）
    """
    # 添加專案根目錄到 Python 路徑
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from youtube_search.services.file_cleanup import FileCleanupService

    logger = setup_logging()

    logger.info("")
    logger.info("*" * 60)
    logger.info(f"清理任務開始: {datetime.now().isoformat()}")
    logger.info("*" * 60)

    try:
        # 初始化清理服務
        cleanup_service = FileCleanupService()

        # 獲取清理前的統計
        stats_before = cleanup_service.get_directory_stats()
        logger.info(
            f"清理前統計: 檔案數={stats_before['total_files']}, 總大小={stats_before['total_size_mb']}MB"
        )

        # 執行清理任務
        result = await cleanup_service.cleanup_task()
        logger.info(f"清理任務結果: {result!r}")

        # 獲取清理後的統計
        stats_after = cleanup_service.get_directory_stats()
        logger.info(
            f"清理後統計: 檔案數={stats_after['total_files']}, 總大小={stats_after['total_size_mb']}MB"
        )

        # 記錄節省的空間
        saved_mb = stats_before["total_size_mb"] - stats_after["total_size_mb"]
        logger.info(f"節省空間: {saved_mb:.2f}MB")

        logger.info("*" * 60)
        logger.info(f"清理任務完成: {datetime.now().isoformat()}")
        logger.info("*" * 60)
        logger.info("")

        return 0

    except Exception as e:
        logger.exception(f"清理任務失敗: {str(e)}")
        logger.info("")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
