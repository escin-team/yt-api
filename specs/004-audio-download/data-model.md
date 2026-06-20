# 數據模型：YouTube 音檔下載 API

**日期**：2025-12-09
**功能**：004-audio-download
**來源**：從 spec.md 的關鍵實體提取

## 核心實體

### 1. DownloadRequest（下載請求）

下載請求實體追蹤單一或批次下載的狀態和元數據。

**屬性**：

| 屬性 | 類型 | 必需 | 描述 | 驗證規則 |
|------|------|------|------|----------|
| video_id | str | 是 | YouTube 影片 ID | 長度 11，僅限字母數字和特定字元 |
| format | str | 否 | 返回格式 | 枚舉：'link', 'stream'，預設 'link' |
| requested_at | datetime | 是 | 請求時間戳記 | ISO 8601 格式 |
| user_id | str | 否 | 使用者識別（未來擴展） | - |
| status | str | 是 | 請求狀態 | 枚舉：'pending', 'processing', 'completed', 'failed' |
| error_message | str | 否 | 錯誤訊息（若失敗） | - |
| processing_time | float | 否 | 處理時間（秒） | >= 0 |

**狀態轉換**：

```
pending → processing → completed
                     ↘ failed
```

**範例（Pydantic 模型）**：

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class DownloadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadFormat(str, Enum):
    LINK = "link"
    STREAM = "stream"

class DownloadRequest(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11)
    format: DownloadFormat = DownloadFormat.LINK
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str | None = None
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: str | None = None
    processing_time: float | None = Field(None, ge=0)
```

---

### 2. AudioFile（音檔）

音檔實體代表已下載和轉換的 MP3 檔案。

**屬性**：

| 屬性 | 類型 | 必需 | 描述 | 驗證規則 |
|------|------|------|------|----------|
| video_id | str | 是 | 對應的 YouTube 影片 ID | 長度 11 |
| file_path | str | 是 | 檔案系統路徑 | 絕對路徑 |
| file_size | int | 是 | 檔案大小（位元組） | > 0 |
| format | str | 是 | 音檔格式 | 固定 'mp3' |
| bitrate | int | 是 | 音質位元率 | 固定 128（kbps） |
| download_url | str | 是 | 公開下載連結 | 有效 URL |
| video_title | str | 是 | 影片標題 | - |
| video_duration | int | 是 | 影片長度（秒） | 1-600 |
| created_at | datetime | 是 | 創建時間 | ISO 8601 |
| expires_at | datetime | 是 | 過期時間 | created_at + 24小時 |
| is_cached | bool | 是 | 是否來自快取 | 布林值 |

**關係**：

- 與 DownloadRequest 一對一關聯（透過 video_id）

**download_url 構造邏輯**：

```python
from config import settings

def generate_download_url(video_id: str) -> str:
    """
    生成公開下載連結

    格式：{DOWNLOAD_BASE_URL}/{video_id}.mp3
    範例：http://localhost:8441/downloads/dQw4w9WgXcQ.mp3
    """
    return f"{settings.DOWNLOAD_BASE_URL}/{video_id}.mp3"
```

**URL 有效性**：

- 連結在音檔創建後立即可用
- 有效期限與檔案 TTL 相同（24 小時）
- Redis 快取過期時，定期清理任務會同步刪除檔案
- 訪問已過期 URL 將返回 404 Not Found

**範例（Pydantic 模型）**：

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timedelta

class AudioFile(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11)
    file_path: str
    file_size: int = Field(..., gt=0)
    format: str = Field(default="mp3")
    bitrate: int = Field(default=128)
    download_url: HttpUrl
    video_title: str
    video_duration: int = Field(..., ge=1, le=600)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    is_cached: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "file_path": "/tmp/youtube_audio/dQw4w9WgXcQ.mp3",
                "file_size": 3145728,
                "format": "mp3",
                "bitrate": 128,
                "download_url": "https://api.example.com/downloads/dQw4w9WgXcQ.mp3",
                "video_title": "Example Video Title",
                "video_duration": 240,
                "created_at": "2025-12-09T10:00:00Z",
                "expires_at": "2025-12-10T10:00:00Z",
                "is_cached": False,
            }
        }
```

---

### 3. DownloadLog（下載日誌）

下載日誌實體記錄所有下載活動，用於監控和審計。

**屬性**：

| 屬性 | 類型 | 必需 | 描述 | 驗證規則 |
|------|------|------|------|----------|
| log_id | str | 是 | 唯一日誌 ID | UUID |
| video_id | str | 是 | 影片 ID | 長度 11 |
| client_ip | str | 是 | 客戶端 IP 位址 | IPv4 或 IPv6 |
| video_duration | int | 否 | 影片長度（秒） | >= 0 |
| is_live_stream | bool | 是 | 是否為串流影片 | 布林值 |
| requested_at | datetime | 是 | 請求時間 | ISO 8601 |
| completed_at | datetime | 否 | 完成時間 | ISO 8601 |
| status | str | 是 | 最終狀態 | 同 DownloadStatus |
| error_message | str | 否 | 錯誤訊息 | - |
| error_type | str | 否 | 錯誤類型 | 枚舉：見下方 |
| file_size | int | 否 | 檔案大小（若成功） | > 0 |
| used_cache | bool | 是 | 是否使用快取 | 布林值 |
| processing_time | float | 否 | 處理時間（秒） | >= 0 |

**錯誤類型枚舉**：

```python
class DownloadErrorType(str, Enum):
    VIDEO_NOT_FOUND = "video_not_found"
    DURATION_EXCEEDED = "duration_exceeded"
    LIVE_STREAM = "live_stream"
    DOWNLOAD_FAILED = "download_failed"
    STORAGE_FULL = "storage_full"
    RESTRICTED = "restricted"
    TIMEOUT = "timeout"
```

**範例（Pydantic 模型）**：

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class DownloadLog(BaseModel):
    log_id: UUID = Field(default_factory=uuid4)
    video_id: str = Field(..., min_length=11, max_length=11)
    client_ip: str = Field(..., description="客戶端 IP 位址")
    video_duration: int | None = Field(None, ge=0)
    is_live_stream: bool = False
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: DownloadStatus
    error_message: str | None = None
    error_type: DownloadErrorType | None = None
    file_size: int | None = Field(None, gt=0)
    used_cache: bool = False
    processing_time: float | None = Field(None, ge=0)
```

---

## API 請求/回應模型

### 4. DownloadAudioRequest（API 請求）

單一影片下載請求的輸入模型。

```python
class DownloadAudioRequest(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11, description="YouTube 影片 ID")
    format: DownloadFormat = Field(
        default=DownloadFormat.LINK,
        description="返回格式：link（下載連結）或 stream（直接串流）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "format": "link"
            }
        }
```

### 5. BatchDownloadRequest（批次下載請求）

批次下載的輸入模型。

```python
class BatchDownloadRequest(BaseModel):
    video_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="影片 ID 列表，最多 20 個"
    )

    @validator('video_ids')
    def validate_video_ids(cls, v):
        for vid in v:
            if len(vid) != 11:
                raise ValueError(f"Invalid video_id: {vid}")
        return v
```

### 6. DownloadAudioResponse（下載回應）

單一影片下載的回應模型。

```python
class DownloadAudioResponse(BaseModel):
    video_id: str
    download_url: HttpUrl | None = Field(
        None,
        description="公開下載連結（format=link 時提供）"
    )
    file_size: int = Field(..., gt=0, description="檔案大小（位元組）")
    video_title: str
    video_duration: int = Field(..., ge=1, le=600)
    format: str = Field(default="mp3")
    bitrate: int = Field(default=128)
    expires_at: datetime
    cached: bool = Field(description="是否來自快取")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "download_url": "https://api.example.com/downloads/dQw4w9WgXcQ.mp3",
                "file_size": 3145728,
                "video_title": "Example Video",
                "video_duration": 240,
                "format": "mp3",
                "bitrate": 128,
                "expires_at": "2025-12-10T10:00:00Z",
                "cached": False
            }
        }
```

### 7. BatchDownloadResponse（批次下載回應）

```python
class BatchDownloadItem(BaseModel):
    video_id: str
    status: str = Field(description="'success' 或 'failed'")
    download_url: HttpUrl | None = None
    file_size: int | None = None
    video_title: str | None = None
    error_message: str | None = None
    error_type: DownloadErrorType | None = None

class BatchDownloadResponse(BaseModel):
    total: int = Field(description="總請求數")
    successful: int = Field(description="成功數")
    failed: int = Field(description="失敗數")
    results: list[BatchDownloadItem]
```

---

## Redis 快取結構

### 快取鍵格式

```
audio:{video_id}
```

### 快取值（JSON）

```json
{
  "file_path": "/tmp/youtube_audio/dQw4w9WgXcQ.mp3",
  "file_size": 3145728,
  "video_title": "Example Video",
  "video_duration": 240,
  "created_at": "2025-12-09T10:00:00Z",
  "expires_at": "2025-12-10T10:00:00Z"
}
```

### TTL

- 24 小時（86400 秒）

---

## 數據流轉

### 下載流程

```
1. 請求到達 → DownloadRequest (pending)
2. 檢查快取 → 查詢 Redis audio:{video_id}
3. 若命中 → AudioFile (cached=True) → 回應
4. 若未命中：
   a. 驗證影片 → yt-dlp extract_info
   b. 下載轉換 → DownloadRequest (processing)
   c. 儲存檔案 → 檔案系統
   d. 快取索引 → Redis setex
   e. 建立 AudioFile
   f. 更新狀態 → DownloadRequest (completed)
   g. 記錄日誌 → DownloadLog
5. 回應客戶端
```

### 清理流程

```
1. 定期任務啟動（每日凌晨2點）
2. 掃描 Redis → keys audio:*
3. 收集有效檔案路徑
4. 掃描下載目錄
5. 刪除孤立檔案（不在 Redis 中的檔案）
6. Redis 自動刪除過期鍵（TTL）
```

---

## 驗證規則

### 影片 ID 驗證

```python
import re

VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')

def validate_video_id(video_id: str) -> bool:
    return bool(VIDEO_ID_PATTERN.match(video_id))
```

### 影片長度驗證

```python
MAX_DURATION = 600  # 10 分鐘

def validate_duration(duration: int) -> bool:
    return 0 < duration <= MAX_DURATION
```

### 檔案大小驗證

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB（10分鐘音檔的合理上限）

def validate_file_size(file_size: int) -> bool:
    return 0 < file_size <= MAX_FILE_SIZE
```

---

## 下一步

1. ✅ 數據模型已定義
2. ➡️ 創建 OpenAPI 合約（contracts/openapi.yaml）
3. ➡️ 編寫快速入門指南（quickstart.md）
