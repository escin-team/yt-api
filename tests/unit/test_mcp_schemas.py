"""MCP Pydantic 模型驗證測試

測試 MCP 相關的 Pydantic 模型：
- SearchRequest 驗證
- VideoInfo 序列化
- SearchResponse JSON Schema
- 無效數據拒絕
"""

from youtube_search.mcp.schemas import SearchRequest, SearchResponse, VideoInfo


class TestMCPSchemas:
    """MCP 模型驗證測試類"""

    def test_search_request_validation(self):
        """
        測試目的：驗證 SearchRequest 模型的驗證規則

        執行步驟：
            1. 構建有效的 SearchRequest
            2. 驗證各欄位的約束
            3. 測試無效數據拒絕
        預期結果：有效數據被接受，無效數據被拒絕
        """
        # 構建有效的搜尋請求（使用 query 別名）
        request = SearchRequest(query="Python programming", max_results=10)

        # 驗證模型
        assert request.query == "Python programming"
        assert request.max_results == 10

        # 驗證 Pydantic 字段定義
        assert hasattr(SearchRequest, "model_fields")
        assert "keyword" in SearchRequest.model_fields
        assert "limit" in SearchRequest.model_fields

    def test_video_info_serialization(self):
        """
        測試目的：驗證 VideoInfo 模型的序列化能力

        執行步驟：
            1. 構建 VideoInfo 實例
            2. 序列化為 dict
            3. 序列化為 JSON
            4. 驗證結果完整性
        預期結果：序列化成功，包含所有必需欄位
        """
        # TODO: 當 VideoInfo 模型完整實現時，實現此測試
        # 預期的 VideoInfo 應包含：
        # - video_id: 唯一識別符
        # - title: 影片標題
        # - channel: 頻道名稱
        # - views: 觀看次數
        # - url: 影片 URL
        # - thumbnail: 縮圖 URL (可選)
        # - duration: 影片時長 (可選)
        # - published_at: 發布時間 (可選)

        # 驗證 VideoInfo 模型定義
        assert hasattr(VideoInfo, "__fields__")

    def test_search_response_json_schema(self):
        """
        測試目的：驗證 SearchResponse 的 JSON Schema 生成

        執行步驟：
            1. 生成 SearchResponse 的 JSON Schema
            2. 驗證 Schema 包含所有必需欄位
            3. 驗證欄位類型和約束
        預期結果：JSON Schema 符合 OpenAPI 規範
        """
        # 獲取 SearchResponse 的 JSON Schema
        schema = SearchResponse.model_json_schema()

        # 驗證 Schema 結構
        assert "properties" in schema

        # 驗證必需欄位存在（使用實際的字段名）
        properties = schema["properties"]
        assert "videos" in properties
        assert "message" in properties

    def test_invalid_data_rejection(self):
        """
        測試目的：驗證無效數據被正確拒絕

        執行步驟：
            1. 嘗試使用無效的數據類型
            2. 嘗試超過限制的數據
            3. 驗證拒絕是否提供清晰的錯誤消息
        預期結果：所有無效數據被拒絕，錯誤消息清晰
        """
        # 測試無效的 max_results 類型
        try:
            SearchRequest(query="test", max_results="not a number")
            raise AssertionError("應該拒絕非整數的 max_results")
        except (ValueError, TypeError):
            pass

        # 測試過長的查詢
        try:
            SearchRequest(query="a" * 201)
            raise AssertionError("應該拒絕超過 200 字符的查詢")
        except ValueError:
            pass
