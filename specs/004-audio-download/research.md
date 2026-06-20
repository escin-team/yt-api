# 技術研究：YouTube 音檔下載 API

**日期**：2025-12-09
**功能**：004-audio-download
**狀態**：已完成

## 研究目標

針對 YouTube 音檔下載功能的關鍵技術決策進行研究，解決規格中標記為「需要澄清」的技術問題。

## 研究項目

### 1. yt-dlp 集成策略

**決策**：使用 yt-dlp 作為 Python 庫（而非 CLI）

**理由**：

- 符合 Constitution IV（簡單優先）
- POC 階段優先快速失敗，不浪費資源
- 避免長時間阻塞 API 請求（5 分鐘逾時已足夠）
- yt-dlp 內部已有 HTTP 連線重試機制
- 暑時性失敗（網路問題）用戶可手動重試
- 永久性失敗（影片不存在、限制）重試無意義

**替代方案考慮**：

- CLI 方式：較簡單但錯誤處理和控制受限
- youtube-dl：已過時，不再維護

**實作方法**：

```python
import yt_dlp

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
    'outtmpl': '/path/to/downloads/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(video_url, download=True)
```

### 2. 影片長度驗證策略

**決策**：在下載前透過 yt-dlp 的 extract_info 獲取元數據

**理由**：

- extract_info 可以不下載只獲取元數據（download=False）
- 包含 duration 欄位（秒為單位）
- 同時可檢測串流狀態（is_live 欄位）
- API 回應快速（通常 <3 秒）
- 版權/年齡/地區限制由 yt-dlp 下載時自動處理，失敗即返回錯誤

**實作方法**：

```python
with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
    info = ydl.extract_info(video_url, download=False)
    duration = info.get('duration', 0)  # 秒
    is_live = info.get('is_live', False)

    if is_live:
        raise LiveStreamError()
    if duration > 600:  # 10 分鐘 = 600 秒
        raise DurationExceedsLimitError()
```

### 3. 快取管理策略

**決策**：結合檔案系統和 Redis 的混合快取

**理由**：

- Redis 儲存快速索引（video_id → 檔案路徑和元數據）
- 檔案系統儲存實際音檔
- Redis TTL 自動處理過期（24小時）
- 檔案清理透過定期任務掃描並刪除孤立檔案

**實作方法**：

```python
# Redis 鍵結構
cache_key = f"audio:{video_id}"
cache_data = {
    "file_path": "/path/to/file.mp3",
    "file_size": 1234567,
    "created_at": timestamp,
    "video_title": "...",
}
redis.setex(cache_key, 86400, json.dumps(cache_data))  # 24小時

# 檔案清理任務（每日執行）
def cleanup_orphaned_files():
    all_keys = redis.keys("audio:*")
    valid_paths = {json.loads(redis.get(k))["file_path"] for k in all_keys}

    for file in os.listdir(DOWNLOAD_DIR):
        if file not in valid_paths:
            os.remove(file)
```

**替代方案考慮**：

- 純檔案系統：需要自行實現過期檢查
- 純 Redis：不適合儲存大型二進制檔案
- 資料庫：過度設計，增加複雜度

### 4. 公開下載連結生成

**決策**：使用 FastAPI StaticFiles 提供公開下載連結

**理由**：

- FastAPI 內建功能，無需額外依賴
- 配置簡單，適合 POC 階段
- 透過 Docker volume 掛載，host 可直接訪問檔案
- 可配合 Nginx 反向代理實現生產環境優化
- 使用 video_id 作為檔名保證唯一性
- 無需額外認證層（符合規格要求）
- 24小時後自動清理符合安全要求

**實作方法**：

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 掛載靜態檔案目錄
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")
```

**URL 構造邏輯**：

```python
def generate_download_url(video_id: str, base_url: str) -> str:
    """生成公開下載連結"""
    return f"{base_url}/{video_id}.mp3"

# 範例：
# base_url = "http://localhost:8441/downloads"
# video_id = "dQw4w9WgXcQ"
# 結果：http://localhost:8441/downloads/dQw4w9WgXcQ.mp3
```

**安全考量**：

- 檔案命名使用驗證過的 video_id（長度 11，字母數字）
- 目錄僅包含音檔，無其他敏感檔案
- Docker volume 掛載限制訪問範圍
- **Rate Limiting 防護**：
  - 下載 API：每 IP 每小時最多 20 次請求
  - 靜態檔案：每 IP 每分鐘最多 60 次訪問
  - 使用 slowapi 實作 IP-based rate limiting
  - 超過限制返回 HTTP 429 Too Many Requests
- 完整的訪問日誌記錄（IP、時間、video_id）

**Docker 配置**：

- 容器內路徑：`/app/downloads`
- Host 掛載：`./scripts/downloads`
- 環境變數：`DOWNLOAD_DIR`、`DOWNLOAD_BASE_URL`

**原實作方法（保留參考）**：

```python
from fastapi.staticfiles import StaticFiles

app.mount("/downloads", StaticFiles(directory="/path/to/downloads"), name="downloads")

# 生成連結
download_url = f"{BASE_URL}/downloads/{video_id}.mp3"
```

### 5. 串流 vs 連結回應

**決策**：使用 FastAPI FileResponse 實作串流

**理由**：

- format=stream：使用 FileResponse 直接串流檔案（自動處理分塊傳輸）
- format=link：返回 JSON 包含公開 URL
- 兩種方式都使用相同的快取檔案
- FileResponse 比 StreamingResponse 更簡單且自動優化
- 支援 Range requests（斷點續傳）

**實作方法**：

```python
from fastapi.responses import FileResponse, JSONResponse

# format=stream: 使用 FileResponse 直接串流
if format == "stream":
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=f"{video_title}.mp3"
    )
else:  # link
    return JSONResponse({
        "video_id": video_id,
        "download_url": f"{BASE_URL}/downloads/{video_id}.mp3",
        "file_size": file_size,
        "expires_at": expires_timestamp,
    })
```

### 6. 下載逾時機制

**決策**：使用 asyncio.wait_for 設定 5 分鐘逾時

**理由**：

- 影片限制 10 分鐘，下載時間理論上不會太長
- 5 分鐘逾時足夠處理網路波動
- 避免無限期佔用資源
- 逾時後拋出 asyncio.TimeoutError，轉換為 DownloadFailedError

**實作方法**：

```python
import asyncio

async def download_with_timeout(video_id: str, timeout: int = 300):
    try:
        result = await asyncio.wait_for(
            download_sync(video_id),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise DownloadFailedError(f"下載逾時（超過 {timeout} 秒）")
```

### 7. 並發下載處理

**決策**：使用 asyncio 搭配 ProcessPoolExecutor

**理由**：

- yt-dlp 下載是 CPU 密集型操作（音檔轉換）
- ProcessPoolExecutor 避免 GIL 限制
- asyncio 保持 API 回應性
- 可限制並發數（使用 Semaphore）

**實作方法**：

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

executor = ProcessPoolExecutor(max_workers=10)

async def download_audio(video_id):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        _download_sync,  # 同步下載函數
        video_id
    )
```

### 7. 錯誤處理與重試

**決策**：單次嘗試，明確錯誤分類

**理由**：

- 符合規格要求（最多嘗試一次）
- yt-dlp 內部已有重試機制
- 明確區分錯誤類型便於客戶端處理
- 避免長時間阻塞

**錯誤分類**：

```python
class VideoNotFoundError(AppError):
    status_code = 404

class DurationExceedsLimitError(AppError):
    status_code = 400

class LiveStreamError(AppError):
    status_code = 400

class DownloadFailedError(AppError):
    status_code = 503

class StorageFullError(AppError):
    status_code = 507
```

### 8. 安全性考量

**決策**：使用 IP-based Rate Limiting + 日誌監控防止濫用

**核心問題**：公開下載連結無需認證可能導致濫用、配額耗盡、儲存空間攻擊

**選擇方案**：IP-based Rate Limiting（平衡簡單性與安全性）

**理由**：

- 符合 POC 簡單原則（Constitution IV）
- 有效防止單一來源濫用
- 實作簡單，使用成熟的 slowapi 庫
- 不影響正常用戶體驗
- 可漸進式升級到更複雜的防護機制

**關鍵措施**：

1. **Rate Limiting**：
   - 下載 API：每 IP 每小時 20 次請求
   - 靜態檔案：每 IP 每分鐘 60 次訪問
   - 超過限制返回 HTTP 429 Too Many Requests
   - 使用 slowapi 庫實作（簡單、成熟）

2. **輸入驗證**：
   - video_id 嚴格驗證（長度 11，字母數字和特定字元）
   - 影片長度限制（<= 600 秒）防止大檔案

3. **資源保護**：
   - 快取機制避免重複下載
   - 定期清理過期檔案（24 小時 TTL）
   - 遵守 YouTube API 配額限制

4. **可觀察性**：
   - 記錄所有下載活動（IP、時間、video_id、狀態）
   - DownloadLog 包含 IP 位址欄位
   - 便於審計和異常檢測

**實作方法**：

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在下載端點應用 rate limit
@app.post("/api/v1/download/audio")
@limiter.limit("20/hour")
async def download_audio(request: Request, ...):
    ...
```

## 依賴項決策

### 新增依賴

1. **yt-dlp** (必須 - Python 套件)
   - 版本：>= 2023.12.0
   - 用途：影片下載和音檔轉換
   - 安裝：`uv add yt-dlp>=2023.12.0`

2. **slowapi** (必須 - Python 套件)
   - 版本：>= 0.1.9
   - 用途：IP-based rate limiting
   - 安裝：`uv add slowapi>=0.1.9`

3. **FFmpeg** (必須 - 系統依賴)
   - **關鍵**：yt-dlp 的音檔轉換功能完全依賴 FFmpeg
   - 沒有 FFmpeg 將導致音檔轉換失敗
   - 安裝方式：
     - Linux/Docker：`apt-get install -y ffmpeg`
     - macOS：`brew install ffmpeg`
     - 驗證：`ffmpeg -version`
   - Dockerfile 必須包含 FFmpeg 安裝步驟

### 現有依賴（復用）

1. **FastAPI**：API 端點和靜態檔案服務
2. **Redis**：快取索引和 TTL 管理
3. **Pydantic**：數據驗證和模型
4. **pytest**：測試框架

## 配置決策

### 新增配置項

```python
# config.py
class Settings(BaseSettings):
    # 下載配置
    DOWNLOAD_DIR: str = "/tmp/youtube_audio"
    MAX_VIDEO_DURATION: int = 600  # 秒
    AUDIO_BITRATE: str = "128"
    AUDIO_FORMAT: str = "mp3"

    # 快取配置
    CACHE_TTL: int = 86400  # 24小時
    MAX_CONCURRENT_DOWNLOADS: int = 10

    # 清理配置
    CLEANUP_SCHEDULE: str = "0 2 * * *"  # 每天凌晨2點

    # 限制配置
    BATCH_DOWNLOAD_LIMIT: int = 20
    DOWNLOAD_TIMEOUT: int = 300  # 5分鐘
```

## 風險與緩解

### 風險 1：yt-dlp API 變更

- **緩解**：固定依賴版本，定期測試更新
- **監控**：記錄 yt-dlp 錯誤，設置警報

### 風險 2：儲存空間耗盡

- **緩解**：實作磁碟空間檢查，在接近限制時拒絕新下載
- **監控**：記錄儲存使用情況

### 風險 3：YouTube 限制

- **緩解**：遵守速率限制，使用快取減少請求
- **監控**：記錄 403/429 錯誤

### 風險 4：音檔轉換失敗

- **緩解**：確保 FFmpeg 正確安裝，記錄詳細錯誤
- **監控**：追蹤轉換成功率

## 下一步

1. ✅ 技術決策已完成
2. ➡️ Phase 1：定義數據模型（data-model.md）
3. ➡️ Phase 1：創建 API 合約（contracts/openapi.yaml）
4. ➡️ Phase 1：編寫快速入門指南（quickstart.md）
