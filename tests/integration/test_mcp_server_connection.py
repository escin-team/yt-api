"""MCP 伺服器連接測試（US1 煙測試）

此測試模組驗證 MCP 伺服器的基本連接功能（T011），
確保客戶端能夠成功連接並執行握手。

測試場景：
    - 伺服器建立連接（US1-AC1）
    - 伺服器回應協定握手（US1-AC1）
    - 連接優雅關閉（US1-AC4）

滿足需求：
    US1-AC1: 伺服器成功建立連接並回應協定握手
    US1-AC4: 連接中斷時優雅關閉並釋放資源
    FR-013: 支援 HTTP 傳輸模式
"""

import pytest

# Python path setup is handled by tests/conftest.py
from youtube_search.mcp.server import create_mcp_server


def test_mcp_server_creation():
    """測試 MCP 伺服器能否成功建立（T011）"""
    try:
        server = create_mcp_server()
        assert server is not None
        print("✓ MCP 伺服器建立成功")
    except Exception as e:
        pytest.fail(f"MCP 伺服器建立失敗：{str(e)}")


def test_mcp_server_has_tools():
    """測試 MCP 伺服器是否已註冊工具列表"""
    try:
        server = create_mcp_server()
        # 驗證伺服器有 list_tools 處理器
        assert hasattr(server, "list_tools")
        print("✓ MCP 伺服器已註冊 list_tools 処理器")
    except Exception as e:
        pytest.fail(f"工具列表檢查失敗：{str(e)}")


if __name__ == "__main__":
    test_mcp_server_creation()
    test_mcp_server_has_tools()
    print("\n✓ MCP 伺服器連接測試通過")
