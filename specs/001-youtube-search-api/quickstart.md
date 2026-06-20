# 快速啟動指南：YouTube 搜尋 API

**版本**：1.0 | **日期**：2025-12-07 | **狀態**：就緒

**語言**：本文件使用正體中文撰寫

## 概述

YouTube 搜尋 API 是一個輕量級 REST 服務，透過爬蟲 YouTube 搜尋結果頁面，提取影片元數據並返回。無需官方 API 金鑰，完全開源實現。

## 先決條件

- Python 3.12+
- Redis 伺服器（快取層，可選但建議用於生產環境）
- pip 或 uv（Python 包管理）

## 安裝

### 1. 複製倉庫

```bash
git clone git@github.com:sacahan/YTSearch.git
cd YTSearch
```

### 2. 建立虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安裝依賴

使用 `uv` 安裝專案依賴（推薦）：

```bash
uv sync
```

或使用傳統 pip：

```bash
pip install -e ".[dev]"
```

**依賴列表**（自 `pyproject.toml`）：

**核心依賴**：

- fastapi >= 0.104.0
- pydantic >= 2.0.0
- pydantic-settings >= 2.0.0
- requests >= 2.31.0
- redis >= 5.0.0
- python-dotenv >= 1.0.0
- uvicorn >= 0.24.0

**開發依賴** (可選，`uv sync --all-extras`)：

- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- pytest-cov >= 4.1.0
- ruff >= 0.1.0
- mypy >= 1.7.0
- black >= 23.12.0

## 環境配置

建立 `.env` 檔案於專案根目錄：

```dotenv
# YouTube 爬蟲配置
YOUTUBE_BASE_URL=https://www.youtube.com/results
YOUTUBE_TIMEOUT=10

# Redis 快取配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true

# API 伺服器配置
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info

# 功能開關
ENABLE_CACHE=true
ENABLE_LOGGING=true
```

若未設定環境變數，使用預設值：

| 變數 | 預設值 |
|------|--------|
| REDIS_HOST | localhost |
| REDIS_PORT | 6379 |
| REDIS_DB | 0 |
| API_PORT | 8000 |

## 啟動服務

### 本地開發模式

```bash
python main.py
```

服務將於 `http://localhost:8000` 啟動。

### 互動式文檔

訪問 `http://localhost:8000/docs` 查看 Swagger UI 互動式文檔。

## 基本使用

### 示例 1：簡單搜尋

```bash
curl -X GET "http://localhost:8000/api/v1/search?keyword=Python教學"
```

**回應**：

```json
{
  "search_keyword": "Python教學",
  "result_count": 1,
  "videos": [
    {
      "video_id": "abc123def456",
      "title": "Python 基礎教學",
      "url": "https://www.youtube.com/watch?v=abc123def456",
      "channel": "教學頻道",
      "channel_url": "https://www.youtube.com/c/example",
      "publish_date": "2024-01-15T10:30:00Z",
      "view_count": 50000,
      "description": "從入門到精通..."
    }
  ],
  "timestamp": "2025-12-07T12:00:00Z"
}
```

### 示例 2：指定結果數量

```bash
curl -X GET "http://localhost:8000/api/v1/search?keyword=Python&limit=5"
```

返回最多 5 筆結果。

### 示例 3：按日期排序

```bash
curl -X GET "http://localhost:8000/api/v1/search?keyword=Python&sort_by=date&limit=3"
```

按發佈日期新舊排序，返回 3 筆。

### 示例 4：使用 Python 客戶端

```python
import requests

API_URL = "http://localhost:8000/api/v1/search"

response = requests.get(API_URL, params={
    "keyword": "張學友 吻別",
    "limit": 5,
    "sort_by": "relevance"
})

if response.status_code == 200:
    data = response.json()
    print(f"搜尋關鍵字：{data['search_keyword']}")
    print(f"結果數量：{data['result_count']}")
    for video in data['videos']:
        print(f"  - {video['title']} ({video['video_id']})")
else:
    print(f"錯誤：{response.status_code} - {response.json()}")
```

## 錯誤處理

### HTTP 400：無效參數

```json
{
  "error": "keyword 為必須參數",
  "error_code": "MISSING_PARAMETER"
}
```

**常見原因**：

- 缺少 `keyword` 參數
- `keyword` 長度超過 200 字元
- `limit` 超過 100 或小於 1

### HTTP 503：服務不可用

```json
{
  "error": "YouTube 搜尋服務暫時無法連接",
  "error_code": "YOUTUBE_UNAVAILABLE"
}
```

**常見原因**：

- YouTube 伺服器暫時不可達
- 網路連線中斷
- IP 被 YouTube 暫時限流

**解決方案**：

1. 檢查網路連線
2. 稍候再試（建議 30 秒後）
3. 確認沒有過多請求（每分鐘建議 < 60 個不同關鍵字）

## 快取機制

- **啟用快取**：同一關鍵字搜尋結果在 Redis 中快取 1 小時
- **快取鍵格式**：`youtube_search:{sha256_hash_of_keyword}`
- **跳過快取**：（目前不支援，預留未來功能）

## 效能最佳實踐

1. **首次搜尋** (~3 秒)：爬蟲 YouTube 頁面
2. **後續搜尋** (~10 毫秒)：從 Redis 讀取快取
3. **推薦批量查詢限制**：每分鐘 < 60 個不同關鍵字

## 開發與測試

### 執行單元測試

```bash
pytest tests/unit/ -v
```

### 執行整合測試

```bash
pytest tests/integration/ -v
```

### 檢查代碼風格

```bash
ruff check src/
```

### 類型檢查

```bash
mypy src/
```

## Docker 部署（可選）

### 構建映像

```bash
docker build -t youtube-search-api:latest .
```

### 執行容器

```bash
docker run -p 8000:8000 \
  -e REDIS_HOST=redis-host \
  -e REDIS_PORT=6379 \
  youtube-search-api:latest
```

## 常見問題

### Q：為什麼沒有使用官方 YouTube Data API？

**A**：官方 API 有配額限制（每天 10,000 單位）且需付費。此實現使用公開網頁爬蟲，成本為零但依賴 YouTube 頁面結構穩定性。

### Q：搜尋結果會被儲存嗎？

**A**：否。系統僅快取結果 1 小時用於效能優化，不進行長期儲存。所有資料均符合 YouTube ToS（不下載/儲存媒體內容）。

### Q：支援分頁嗎？

**A**：目前不支援（P2 功能）。`limit` 參數限制單次返回結果至最多 100 筆，對應 YouTube 首頁結果數。

### Q：如何處理中文特殊字符？

**A**：系統完全支援 UTF-8 編碼，包括中文、表情符號等。關鍵字自動 URL 編碼。

## 故障排除

### Redis 連線失敗

```python
ConnectionRefusedError: [Errno 111] Connection refused
```

**解決方案**：

1. 確認 Redis 服務執行中：`redis-cli ping`
2. 檢查 `REDIS_HOST` 和 `REDIS_PORT` 環境變數
3. 設定 `REDIS_ENABLED=false` 暫時禁用快取（不建議用於生產）

### YouTube 搜尋超時

```python
requests.exceptions.Timeout: Connection timeout
```

**解決方案**：

1. 增加超時時間：`YOUTUBE_TIMEOUT=30`
2. 檢查網路連線速度
3. 稍候再試（YouTube 可能暫時限流）

## 支援與反饋

遇到問題或有功能建議，請提交 Issue 至 [GitHub 倉庫](https://github.com/sacahan/YTSearch/issues)。

## 下一步

- 瞭解 [API 規格](./contracts/openapi.yaml)
- 查看 [數據模型](./data-model.md) 詳細定義
- 檢查 [實現計劃](./plan.md) 技術架構
