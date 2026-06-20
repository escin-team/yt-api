# 數據模型設計：YouTube 搜尋 API

**版本**：1.0 | **日期**：2025-12-07 | **狀態**：確定

**語言**：本文件使用正體中文撰寫

## 核心實體

### Video（影片元數據）

代表 YouTube 搜尋結果中的單個影片記錄。

**主要欄位**：

| 欄位 | 類型 | 必須 | 說明 | 範例 |
|------|------|------|------|------|
| `video_id` | string | ✅ | YouTube 影片唯一識別碼 | `abc123def456` |
| `title` | string \| null | ❌ | 影片標題 | `Python 基礎教學` |
| `url` | string \| null | ❌ | 影片完整 URL | `https://www.youtube.com/watch?v=abc...` |
| `channel` | string \| null | ❌ | 頻道名稱 | `教學頻道` |
| `channel_url` | string \| null | ❌ | 頻道 URL | `https://www.youtube.com/c/...` |
| `publish_date` | string \| null | ❌ | 發佈日期（ISO 8601） | `2024-01-15T10:30:00Z` |
| `view_count` | integer \| null | ❌ | 觀看次數 | `50000` |
| `description` | string \| null | ❌ | 影片描述摘要 | `從入門到精通...` |

**數據驗證**：

- `video_id`：正則模式 `^[a-zA-Z0-9_-]{11}$`（YouTube 標準格式）
- `title`：最大 500 字元
- `channel`：最大 200 字元
- `view_count`：非負整數
- `publish_date`：RFC 3339 (ISO 8601) 格式，UTC 時區
- `description`：最大 5000 字元

**失敗處理**：

- 若 `video_id` 無法提取，整筆影片不返回
- 其他欄位若無法提取，設為 null（不影響記錄返回）

**Pydantic 模型定義**：

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class Video(BaseModel):
    """YouTube 影片元數據"""

    video_id: str = Field(
        ...,
        description="YouTube 影片 ID",
        pattern=r"^[a-zA-Z0-9_-]{11}$"
    )
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="影片標題"
    )
    url: Optional[str] = Field(
        None,
        description="影片 URL"
    )
    channel: Optional[str] = Field(
        None,
        max_length=200,
        description="頻道名稱"
    )
    channel_url: Optional[str] = Field(
        None,
        description="頻道 URL"
    )
    publish_date: Optional[str] = Field(
        None,
        description="發佈日期（ISO 8601）"
    )
    view_count: Optional[int] = Field(
        None,
        ge=0,
        description="觀看次數"
    )
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="影片描述"
    )

    @field_validator('publish_date')
    @classmethod
    def validate_publish_date(cls, v: Optional[str]) -> Optional[str]:
        """驗證 ISO 8601 格式"""
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValueError('publish_date 必須為 ISO 8601 格式')
        return v
```

### SearchResult（搜尋結果集合）

代表一次搜尋操作的完整結果。

**主要欄位**：

| 欄位 | 類型 | 必須 | 說明 | 範例 |
|------|------|------|------|------|
| `search_keyword` | string | ✅ | 搜尋關鍵字 | `Python 教學` |
| `result_count` | integer | ✅ | 返回影片數量 | `5` |
| `videos` | list[Video] | ✅ | 影片清單 | `[...]` |
| `timestamp` | string | ✅ | 搜尋時間戳記（ISO 8601 UTC，秒級精度） | `2025-12-07T12:00:00Z` |

**timestamp 格式說明**：

- 格式：RFC 3339 (ISO 8601)
- 時區：UTC（Z 後綴）
- 精度：秒級（YYYY-MM-DDTHH:MM:SSZ）
- 毫秒級不使用（為保持 API 簡潔）
- 範例：`2025-12-07T12:00:00Z`（標準秒級格式）

**數據驗證**：

- `search_keyword`：1-200 字元
- `result_count`：非負整數，範圍 0-100（含 limit 參數）
- `timestamp`：RFC 3339 格式，UTC 時區
- `videos`：至少 0 筆（搜尋無結果時返回空陣列）

**Pydantic 模型定義**：

```python
from typing import List
from datetime import datetime

class SearchResult(BaseModel):
    """搜尋結果"""

    search_keyword: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="搜尋關鍵字"
    )
    result_count: int = Field(
        ...,
        ge=0,
        le=100,
        description="返回影片數量"
    )
    videos: List[Video] = Field(
        default_factory=list,
        description="影片清單"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + 'Z',
        description="搜尋時間戳記"
    )

    @field_validator('result_count')
    @classmethod
    def validate_result_count(cls, v: int, info) -> int:
        """驗證結果數量與 videos 陣列一致"""
        if hasattr(info.data, 'videos'):
            if v != len(info.data['videos']):
                raise ValueError('result_count 必須等於 videos 陣列長度')
        return v
```

## 實體關係

```
SearchResult (1)
    ├─ search_keyword: str
    ├─ result_count: int
    ├─ timestamp: str
    └─ videos (0..*) ──> Video
                         ├─ video_id: str (PK)
                         ├─ title: str | null
                         ├─ channel: str | null
                         └─ ...
```

## 驗證規則摘要

| 實體 | 欄位 | 規則 | 失敗行為 |
|------|------|------|---------|
| Video | video_id | 必須，格式 11 字元 | 拒絕該筆記錄 |
| Video | title | 可選，最大 500 字 | 設為 null |
| Video | channel | 可選，最大 200 字 | 設為 null |
| Video | view_count | 可選，非負整數 | 設為 null |
| SearchResult | search_keyword | 必須，1-200 字 | HTTP 400 |
| SearchResult | result_count | 必須，0-100 | 與 videos 長度一致 |
| SearchResult | videos | 必須，陣列 | 可為空陣列 |
| SearchResult | timestamp | 必須，ISO 8601 | 自動生成 |

## 序列化與反序列化

### JSON 序列化範例

**請求**：`GET /api/v1/search?keyword=Python&limit=2`

**回應** (HTTP 200)：

```json
{
  "search_keyword": "Python",
  "result_count": 2,
  "videos": [
    {
      "video_id": "mIF-nn_y2_8",
      "title": "Python 基礎教學",
      "url": "https://www.youtube.com/watch?v=mIF-nn_y2_8",
      "channel": "教學頻道",
      "channel_url": "https://www.youtube.com/c/example",
      "publish_date": "2024-01-15T10:30:00Z",
      "view_count": 50000,
      "description": "從入門到精通..."
    },
    {
      "video_id": "k6zmy0yvXB4",
      "title": "Python 進階技巧",
      "url": "https://www.youtube.com/watch?v=k6zmy0yvXB4",
      "channel": null,
      "channel_url": null,
      "publish_date": null,
      "view_count": null,
      "description": null
    }
  ],
  "timestamp": "2025-12-07T12:00:00Z"
}
```

### 錯誤回應範例

**HTTP 400**（無效參數）：

```json
{
  "error": "keyword 長度超過 200 字元",
  "error_code": "INVALID_KEYWORD_LENGTH"
}
```

**HTTP 503**（YouTube 不可用）：

```json
{
  "error": "YouTube 搜尋服務暫時無法連接",
  "error_code": "YOUTUBE_UNAVAILABLE"
}
```

## 後續注記

- **快取鍵**：`youtube_search:{sha256(keyword)}`（Redis）
- **快取 TTL**：3600 秒（1 小時）
- **日誌記錄**：所有搜尋請求與錯誤須記錄至結構化日誌
- **版本化**：未來 API 版本升級時，保持向後相容
