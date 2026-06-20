#!/usr/bin/env python3
"""MCP stdio 伺服器入口

此模組提供 stdio 傳輸方式的 MCP 伺服器，用於與 VS Code 等客戶端通訊。
直接通過標準輸入/輸出進行 MCP 協定通訊，無需 HTTP 伺服器。

使用方式：
    python mcp_stdio.py
"""

import asyncio
import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from youtube_search.mcp.tools.youtube_search import YouTubeSearchTool
from youtube_search.utils.logger import get_logger

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)


# 建立 MCP 伺服器
server = Server(name="youtube-search-mcp")

# 初始化工具
youtube_search_tool = YouTubeSearchTool()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出所有可用的工具"""
    logger.info("列出工具")

    return [
        types.Tool(
            name="youtube_search",
            description=youtube_search_tool.description,
            inputSchema=youtube_search_tool.input_schema,
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """調用指定的工具"""
    logger.info(f"調用工具: {name}, 參數: {arguments}")

    if name == "youtube_search":
        result = await youtube_search_tool.execute(arguments)
        return [types.TextContent(type="text", text=str(result))]
    else:
        return [types.TextContent(type="text", text=f"未知工具: {name}", isError=True)]


async def main() -> None:
    """啟動 MCP stdio 伺服器"""
    logger.info("MCP stdio 伺服器啟動中...")

    # 使用 stdio_server context manager 啟動伺服器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP stdio 伺服器已啟動")

        # 執行伺服器，處理所有進來的請求
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="youtube-search-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
