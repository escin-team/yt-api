"""MCP 伺服器工具列表查詢測試（US1 煙測試）

此測試模組驗證 MCP 伺服器的工具列表查詢功能（T012），
確保客戶端能夠取得完整的工具元數據。

測試場景：
    - 列出可用工具（US1-AC2）
    - 工具包含完整描述和參數定義（FR-011）
    - 工具格式符合 MCP 標準（FR-012）

滿足需求：
    US1-AC2: 伺服器返回所有已註冊的搜尋工具及其描述
    FR-002: 自動註冊所有可用工具
    FR-011: 在工具描述中清楚說明參數和限制
    FR-012: 確保 MCP 回應格式符合協定規範
"""

import pytest

# Python path setup is handled by tests/conftest.py
from youtube_search.mcp.server import get_mcp_server_manager


def test_list_tools():
    """測試工具列表查詢功能（T012）"""
    try:
        manager = get_mcp_server_manager()
        # 調用正確的方法名稱
        import asyncio

        tools = asyncio.run(manager._list_tools_handler())

        # 驗證返回的工具列表
        assert isinstance(tools, list)
        assert len(tools) > 0
        print(f"✓ 成功取得 {len(tools)} 個工具")

        # 驗證 youtube_search 工具存在
        tool_names = [t.name for t in tools]
        assert "youtube_search" in tool_names
        print("✓ youtube_search 工具已註冊")

    except Exception as e:
        pytest.fail(f"工具列表查詢失敗：{str(e)}")


def test_youtube_search_tool_metadata():
    """測試 youtube_search 工具的元數據（FR-011, FR-012）"""
    try:
        manager = get_mcp_server_manager()
        import asyncio

        tools = asyncio.run(manager._list_tools_handler())

        # 找到 youtube_search 工具
        youtube_search_tool = None
        for tool in tools:
            if tool.name == "youtube_search":
                youtube_search_tool = tool
                break

        assert youtube_search_tool is not None
        print("✓ youtube_search 工具元數據：")
        print(f"  - 名稱：{youtube_search_tool.name}")
        print(f"  - 描述：{youtube_search_tool.description[:60]}...")

        # 驗證工具有輸入參數定義
        assert youtube_search_tool.inputSchema is not None
        assert isinstance(youtube_search_tool.inputSchema, dict)
        assert "properties" in youtube_search_tool.inputSchema
        print("✓ 工具參數定義完整")

        # 驗證必填參數
        required = youtube_search_tool.inputSchema.get("required", [])
        assert "keyword" in required
        print(f"✓ 必填參數：{required}")

    except Exception as e:
        pytest.fail(f"工具元數據驗證失敗：{str(e)}")


if __name__ == "__main__":
    test_list_tools()
    test_youtube_search_tool_metadata()
    print("\n✓ MCP 工具列表查詢測試通過")
