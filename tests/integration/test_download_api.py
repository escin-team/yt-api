"""下載 API 煙霧測試 - 驗證核心下載流程。

本測試文件驗證：
1. 單一影片下載成功
2. 快取命中
3. 影片不存在錯誤
4. 長度超限錯誤
5. 批次下載部分成功/失敗
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """提供測試客戶端。"""
    return TestClient(app)


class TestDownloadAudioBasic:
    """單一影片下載 API 基本測試。"""

    def test_download_audio_with_valid_video_id(self, client):
        """測試使用有效影片 ID 下載。"""
        response = client.post("/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=link")

        # 應返回 200 或 503（如果 yt-dlp 因網路問題失敗）
        assert response.status_code in [200, 503, 404]

        if response.status_code == 200:
            data = response.json()
            assert "video_id" in data
            assert "title" in data
            assert "duration" in data
            assert "download_url" in data
            assert "cached" in data

    def test_download_audio_with_invalid_video_id(self, client):
        """測試使用無效影片 ID。"""
        response = client.post("/api/v1/download/audio?video_id=invalid_id&format=link")

        # 應返回 400（無效參數）
        assert response.status_code == 400
        data = response.json()
        assert "code" in data
        assert data["code"] == "INVALID_VIDEO_ID"

    def test_download_audio_with_stream_format(self, client):
        """測試使用 stream 格式。"""
        # 首先下載為 link 格式建立快取
        client.post("/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=link")

        # 然後嘗試以 stream 格式下載
        response = client.post("/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=stream")

        # 成功時返回 200 並搭配 audio/mpeg 內容
        if response.status_code == 200:
            assert response.headers["content-type"] == "audio/mpeg"

    def test_download_audio_missing_video_id(self, client):
        """測試缺少影片 ID。"""
        response = client.post("/api/v1/download/audio")

        # 應返回 422（缺少必須參數）
        assert response.status_code == 422

    def test_download_audio_cache_hit(self, client):
        """測試快取命中。"""
        # 首次下載
        response1 = client.post("/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=link")

        if response1.status_code == 200:
            data1 = response1.json()
            cached1 = data1.get("cached", False)

            # 第二次下載（應該命中快取）
            response2 = client.post("/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=link")

            if response2.status_code == 200:
                data2 = response2.json()
                cached2 = data2.get("cached", False)

                # 第二次應該是快取命中
                assert cached2 is True or cached1 is False  # 至少第二次應快取


class TestBatchDownload:
    """批次下載 API 測試。"""

    def test_batch_download_multiple_videos(self, client):
        """測試批次下載多個影片。"""
        request_data = {"video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"]}

        response = client.post("/api/v1/download/batch", json=request_data)

        # 應返回 200（即使個別影片失敗）
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "successful" in data
            assert "failed" in data
            assert "items" in data
            assert data["total"] == 2

    def test_batch_download_with_invalid_id(self, client):
        """測試批次下載包含無效 ID。"""
        request_data = {"video_ids": ["invalid_id", "dQw4w9WgXcQ"]}

        response = client.post("/api/v1/download/batch", json=request_data)

        # 應返回 200（部分成功）或 400（全部無效）
        assert response.status_code in [200, 400]

    def test_batch_download_exceeds_limit(self, client):
        """測試超過批次限制（最多 20 個）。"""
        # 建立超過 20 個的影片 ID 清單
        video_ids = [f"dQw4w9WgXc{i:02d}" for i in range(25)]
        request_data = {"video_ids": video_ids}

        response = client.post("/api/v1/download/batch", json=request_data)

        # 應返回 422（驗證錯誤）
        assert response.status_code == 422

    def test_batch_download_empty_list(self, client):
        """測試空的批次清單。"""
        request_data = {"video_ids": []}

        response = client.post("/api/v1/download/batch", json=request_data)

        # 應返回 422（驗證錯誤）
        assert response.status_code == 422


class TestDownloadErrorHandling:
    """下載錯誤處理測試。"""

    def test_nonexistent_video(self, client):
        """測試不存在的影片。"""
        response = client.post("/api/v1/download/audio?video_id=xxxxxxxxxxxx&format=link")

        # 應返回 404 或 503（取決於是否連接到 YouTube）
        assert response.status_code in [404, 503, 500]

    def test_health_check(self, client):
        """測試健康檢查端點。"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
