#!/usr/bin/env python3
"""測試 MCP stdio 客戶端與伺服器的通訊

此測試啟動 mcp_stdio.py 伺服器並驗證：
1. 伺服器能夠初始化
2. 客戶端能夠列出可用工具
3. 客戶端能夠調用工具
"""

import asyncio
import os
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_mcp_stdio_server():
    """測試 MCP stdio 伺服器"""

    # 使用相對路徑定位 mcp_stdio.py（位於項目根目錄）
    project_root = Path(__file__).parent.parent.parent
    mcp_stdio_path = project_root / "mcp_stdio.py"
    
    # 創建伺服器參數
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", str(mcp_stdio_path)],
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "MCP_SEARCH_TIMEOUT": "15",
        },
    )

    try:
        print("🔌 連接到 MCP 伺服器...")
        async with stdio_client(server_params) as (read, write):
            print("✅ 已連接到 MCP 伺服器")

            async with ClientSession(read, write) as session:
                # 初始化會話
                print("⏳ 初始化會話...")
                await session.initialize()
                print("✅ 會話初始化成功")

                # 列出可用工具
                print("\n⏳ 列出可用工具...")
                tools = await session.list_tools()
                print(f"✅ 找到 {len(tools.tools)} 個工具")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description}")

                # 測試調用工具
                if tools.tools:
                    tool_name = "youtube_search"
                    print(f"\n⏳ 測試調用工具: {tool_name}")

                    test_arguments = {
                        "keyword": "Python",
                        "max_results": 3,
                    }

                    result = await session.call_tool(
                        tool_name,
                        arguments=test_arguments,
                    )
                    print("✅ 工具調用成功")
                    print("   結果摘要:")
                    if result.content:
                        content = result.content[0]
                        text = content.text if hasattr(content, "text") else str(content)
                        # 打印前 500 個字符
                        preview = text[:500] + ("..." if len(text) > 500 else "")
                        print(f"   {preview}")

        print("\n✅ 所有測試通過！")
        return True

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主函數"""
    success = await test_mcp_stdio_server()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
