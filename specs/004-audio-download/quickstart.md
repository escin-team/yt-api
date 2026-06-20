# 快速入門：YouTube 音檔下載 API

**功能**：004-audio-download
**日期**：2025-12-09
**目標使用者**：開發人員

## 概述

本指南將幫助你快速設定並運行 YouTube 音檔下載 API 功能。此功能允許你：

- 下載 YouTube 影片並轉換為 MP3 音檔
- 支援單一和批次下載
- 自動快取管理（24 小時）
- 公開下載連結或直接串流

## 前置需求

### 系統需求

- Python 3.12+
- FFmpeg（音檔轉換必需）
- Redis 伺服器（快取管理）
- 磁碟空間：至少 5GB 可用空間

### 已安裝套件

```bash
# 檢查 Python 版本
python --version  # 應顯示 3.12 或更高

# 檢查 FFmpeg
ffmpeg -version

# 檢查 Redis
redis-cli ping  # 應返回 PONG
```

## 環境設定

### 步驟 1：安裝 FFmpeg

**macOS**：

```bash
brew install ffmpeg
```

**Linux（Ubuntu/Debian）**：

```bash
sudo apt update
sudo apt install ffmpeg
```

**驗證安裝**：

```bash
ffmpeg -version
# 應顯示 FFmpeg 版本資訊
```

### 步驟 2：安裝 Python 依賴

```bash
cd /Users/sacahan/Documents/workspace/YTSearch

# 安裝 yt-dlp
pip install yt-dlp>=2023.12.0

# 驗證安裝
yt-dlp --version
```

### 步驟 3：配置 Redis

**啟動 Redis**：

```bash
# macOS（使用 Homebrew）
brew services start redis

# Linux
sudo systemctl start redis
```

**測試連線**：

```bash
redis-cli ping
# 應返回：PONG
```

### 步驟 4：創建下載目錄

```bash
# 創建音檔儲存目錄
mkdir -p /tmp/youtube_audio

# 設定權限
chmod 755 /tmp/youtube_audio
```

### 步驟 5：環境變數配置

創建或編輯 `.env` 檔案：

```bash
# YouTube 下載配置
DOWNLOAD_DIR=/tmp/youtube_audio
MAX_VIDEO_DURATION=600
AUDIO_BITRATE=128
AUDIO_FORMAT=mp3

# 快取配置
CACHE_TTL=86400
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
BASE_URL=http://localhost:8000
```

## 運行服務

### 啟動 API 伺服器

```bash
# 從專案根目錄
cd /Users/sacahan/Documents/workspace/YTSearch

# 啟動 FastAPI 伺服器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**成功啟動的輸出**：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using statreload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 驗證 API 運行

```bash
# 檢查健康狀態
curl http://localhost:8000/health

# 查看 API 文件
open http://localhost:8000/docs
```

## 使用範例

### 範例 1：下載單一影片音檔（連結模式）

```bash
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "format": "link"
  }'
```

**預期回應**：

```json
{
  "video_id": "dQw4w9WgXcQ",
  "download_url": "http://localhost:8000/downloads/dQw4w9WgXcQ.mp3",
  "file_size": 3145728,
  "video_title": "Rick Astley - Never Gonna Give You Up",
  "video_duration": 213,
  "format": "mp3",
  "bitrate": 128,
  "expires_at": "2025-12-10T10:00:00Z",
  "cached": false
}
```

### 範例 2：直接串流音檔

```bash
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "format": "stream"
  }' \
  --output music.mp3
```

### 範例 3：批次下載多個影片

```bash
curl -X POST http://localhost:8000/api/v1/download/batch \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": [
      "dQw4w9WgXcQ",
      "jNQXAC9IVRw",
      "9bZkp7q19f0"
    ]
  }'
```

**預期回應**：

```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "status": "success",
      "download_url": "http://localhost:8000/downloads/dQw4w9WgXcQ.mp3",
      "file_size": 3145728,
      "video_title": "Rick Astley - Never Gonna Give You Up",
      "error_message": null,
      "error_type": null
    },
    {
      "video_id": "jNQXAC9IVRw",
      "status": "success",
      "download_url": "http://localhost:8000/downloads/jNQXAC9IVRw.mp3",
      "file_size": 456789,
      "video_title": "Me at the zoo",
      "error_message": null,
      "error_type": null
    },
    {
      "video_id": "9bZkp7q19f0",
      "status": "success",
      "download_url": "http://localhost:8000/downloads/9bZkp7q19f0.mp3",
      "file_size": 2345678,
      "video_title": "PSY - GANGNAM STYLE",
      "error_message": null,
      "error_type": null
    }
  ]
}
```

### 範例 4：使用 Python 客戶端

```python
import requests

# API 端點
BASE_URL = "http://localhost:8000/api/v1"

# 下載單一影片
response = requests.post(
    f"{BASE_URL}/download/audio",
    json={
        "video_id": "dQw4w9WgXcQ",
        "format": "link"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"下載連結: {data['download_url']}")
    print(f"檔案大小: {data['file_size']} bytes")
    print(f"影片標題: {data['video_title']}")
else:
    print(f"錯誤: {response.json()}")
```

### 範例 5：批次下載 Python 腳本

```python
import requests
from typing import List

def batch_download_audio(video_ids: List[str]) -> dict:
    """批次下載多個影片音檔"""
    response = requests.post(
        "http://localhost:8000/api/v1/download/batch",
        json={"video_ids": video_ids}
    )
    return response.json()

# 使用範例
video_ids = ["dQw4w9WgXcQ", "jNQXAC9IVRw", "9bZkp7q19f0"]
result = batch_download_audio(video_ids)

print(f"總計: {result['total']}")
print(f"成功: {result['successful']}")
print(f"失敗: {result['failed']}")

# 顯示每個結果
for item in result['results']:
    if item['status'] == 'success':
        print(f"✅ {item['video_id']}: {item['video_title']}")
    else:
        print(f"❌ {item['video_id']}: {item['error_message']}")
```

## 測試快取功能

### 測試快取命中

```bash
# 第一次請求（應該較慢，5-30 秒）
time curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "format": "link"}'

# 第二次請求（應該很快，< 100ms）
time curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "format": "link"}'

# 檢查 cached 欄位（第二次應為 true）
```

### 檢查 Redis 快取

```bash
# 查看所有音檔快取鍵
redis-cli KEYS "audio:*"

# 查看特定快取內容
redis-cli GET "audio:dQw4w9WgXcQ"

# 查看快取 TTL（剩餘時間）
redis-cli TTL "audio:dQw4w9WgXcQ"
```

### 手動清除快取

```bash
# 清除特定影片快取
redis-cli DEL "audio:dQw4w9WgXcQ"

# 清除所有音檔快取
redis-cli KEYS "audio:*" | xargs redis-cli DEL
```

## 錯誤處理測試

### 測試 1：無效的影片 ID

```bash
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"video_id": "invalid123"}'
```

**預期錯誤（400）**：

```json
{
  "error": "invalid_video_id",
  "message": "影片 ID 必須為 11 個字元",
  "video_id": "invalid123"
}
```

### 測試 2：影片不存在

```bash
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"video_id": "notfound123"}'
```

**預期錯誤（404）**：

```json
{
  "error": "video_not_found",
  "message": "找不到指定的影片",
  "video_id": "notfound123"
}
```

### 測試 3：影片過長

使用一個超過 10 分鐘的影片 ID 進行測試。

**預期錯誤（400）**：

```json
{
  "error": "duration_exceeded",
  "message": "影片長度超過 600 秒限制",
  "video_id": "long_video_id",
  "duration": 720,
  "max_duration": 600
}
```

### 測試 4：串流影片

使用一個直播影片 ID 進行測試。

**預期錯誤（403）**：

```json
{
  "error": "live_stream_not_supported",
  "message": "不支援串流或直播影片",
  "video_id": "live_stream_id"
}
```

## 監控和日誌

### 查看即時日誌

```bash
# 查看 API 日誌
tail -f logs/api.log

# 查看下載服務日誌
tail -f logs/download.log
```

### 監控下載目錄

```bash
# 查看下載目錄大小
du -sh /tmp/youtube_audio

# 列出所有下載的檔案
ls -lh /tmp/youtube_audio

# 統計檔案數量
ls -1 /tmp/youtube_audio | wc -l
```

### 監控 Redis 記憶體使用

```bash
# Redis 記憶體資訊
redis-cli INFO memory

# 快取鍵數量
redis-cli DBSIZE
```

## 自動清理

### 手動觸發清理

```bash
# 執行清理腳本（刪除過期檔案）
python -m src.youtube_search.services.cleanup
```

### 設定排程清理（Cron）

```bash
# 編輯 crontab
crontab -e

# 新增每日凌晨 2 點清理任務
0 2 * * * cd /Users/sacahan/Documents/workspace/YTSearch && python -m src.youtube_search.services.cleanup >> logs/cleanup.log 2>&1
```

## 效能調校

### 建議配置

**低流量環境**（< 100 請求/天）：

```bash
DOWNLOAD_DIR=/tmp/youtube_audio
MAX_VIDEO_DURATION=600
CACHE_TTL=86400  # 24 小時
```

**中流量環境**（100-1000 請求/天）：

```bash
DOWNLOAD_DIR=/var/youtube_audio  # 使用更大的磁碟
MAX_VIDEO_DURATION=600
CACHE_TTL=172800  # 48 小時（減少重複下載）
```

**高流量環境**（> 1000 請求/天）：

- 使用獨立的檔案伺服器（如 S3）
- 增加 Redis 記憶體
- 考慮分散式快取
- 使用 CDN 分發下載連結

## 故障排除

### 問題 1：FFmpeg 未找到

**症狀**：

```
ERROR: ffmpeg not found
```

**解決方案**：

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# 驗證
which ffmpeg
```

### 問題 2：Redis 連線失敗

**症狀**：

```
ConnectionError: Error connecting to Redis
```

**解決方案**：

```bash
# 啟動 Redis
brew services start redis

# 檢查 Redis 狀態
redis-cli ping
```

### 問題 3：磁碟空間不足

**症狀**：

```
ERROR: storage_full
```

**解決方案**：

```bash
# 檢查磁碟空間
df -h /tmp

# 手動清理舊檔案
find /tmp/youtube_audio -type f -mtime +1 -delete

# 或執行清理腳本
python -m src.youtube_search.services.cleanup
```

### 問題 4：下載超時

**症狀**：

```
ERROR: download_failed, message: Timeout
```

**解決方案**：

- 檢查網路連線
- 嘗試使用不同的影片
- 增加超時設定（在 config.py 中）

## 下一步

- 📖 閱讀完整 [API 文件](./contracts/openapi.yaml)
- 🗂️ 查看 [數據模型定義](./data-model.md)
- 📋 參考 [實作計畫](./plan.md)
- 🧪 執行整合測試（`pytest tests/integration/test_audio_download.py`）

## 支援

如遇問題，請查看：

- **日誌檔案**：`logs/api.log`, `logs/download.log`
- **Redis 狀態**：`redis-cli INFO`
- **磁碟空間**：`df -h`
- **錯誤代碼**：參考 OpenAPI 規範中的錯誤回應

---

**最後更新**：2025-12-09
**版本**：1.0.0
