# quickstart.md（Phase 1）

## 前置設定

- 準備 `.env`：確認 `REDIS_ENABLED`、`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`、`REDIS_TTL_SECONDS`，預設 TTL 3600 秒。
- 安裝依賴：`uv sync` 或 `pip install -e .`（確保 Python 版本 >=3.12）。
- 啟動 Redis（若 `REDIS_ENABLED=true`）。

## 啟動 API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 呼叫範例

### 基本請求 - 取得播放列表元數據

```bash
curl "http://localhost:8000/api/v1/playlist/metadata" \
  --get \
  --data-urlencode "playlist_url=https://www.youtube.com/playlist?list=PLuOOH93liK-tJiMmA6zW8PdwTmgc4k6bq"
```

### 成功回應 (200)

```json
{
  "playlist_id": "PLuOOH93liK-tJiMmA6zW8PdwTmgc4k6bq",
  "url": "https://www.youtube.com/playlist?list=PLuOOH93liK-tJiMmA6zW8PdwTmgc4k6bq",
  "title": "Learn Python - Full Course",
  "video_count": 150,
  "partial": false,
  "fetched_at": "2025-12-08T10:30:45Z",
  "tracks": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Python Basics - Part 1",
      "channel": "Tech Academy",
      "channel_url": "https://www.youtube.com/channel/UCXXXXXXXX",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "publish_date": "2 years ago",
      "duration": "45:30",
      "view_count": 1000000,
      "position": 1
    }
  ]
}
```

### 強制重新爬取 (跳過快取)

```bash
curl "http://localhost:8000/api/v1/playlist/metadata" \
  --get \
  --data-urlencode "playlist_url=https://www.youtube.com/playlist?list=PLuOOH93liK-tJiMmA6zW8PdwTmgc4k6bq" \
  --data-urlencode "force_refresh=true"
```

## Partial 標記說明

當 `partial=true` 時，表示播放列表是**不完整的**。可能原因：

- **TIMEOUT**: 爬取超過 30 秒時間限制，已回傳部分結果
- **BATCH_LIMIT_EXCEEDED**: 達到 15 批 continuation 上限，已回傳部分結果
- **CONTINUATION_ERROR**: Continuation 請求失敗

**重要**：`partial=true` 的結果 **不被快取**，下次請求將重新爬取。

### Partial 回應範例

```json
{
  "playlist_id": "PLlarge_list",
  "title": "Very Long Playlist",
  "video_count": 5000,
  "partial": true,
  "fetched_at": "2025-12-08T10:35:00Z",
  "tracks": [
    { "video_id": "vid1", "title": "Track 1", ... },
    { "video_id": "vid2", "title": "Track 2", ... },
    ...
  ]
}
```

## 錯誤回應

### 400 - 無效 URL

```bash
curl "http://localhost:8000/api/v1/playlist/metadata" \
  --get \
  --data-urlencode "playlist_url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

回應：

```json
{
  "code": "INVALID_PARAMETER",
  "message": "playlist_url 缺少 list 參數",
  "reason": null,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "playlist_id": null,
  "status": 400
}
```

### 403 - 私密播放列表

```json
{
  "code": "PLAYLIST_FORBIDDEN",
  "message": "播放列表私密或無法存取",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": 403
}
```

### 404 - 播放列表不存在

```json
{
  "code": "PLAYLIST_NOT_FOUND",
  "message": "播放列表不存在",
  "trace_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": 404
}
```

### 410 - 播放列表已刪除

```json
{
  "code": "PLAYLIST_GONE",
  "message": "播放列表已刪除",
  "trace_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": 410
}
```

### 502 - 爬取失敗

```json
{
  "code": "PLAYLIST_SCRAPING_ERROR",
  "message": "無法從 YouTube 提取播放列表資料",
  "reason": "ytInitialData 提取失敗",
  "trace_id": "550e8400-e29b-41d4-a716-446655440004",
  "status": 502
}
```

## 快取行為

- **命中快取**：對相同 `playlist_id` 的連續請求會使用緩存（第 2 次及之後），延遲通常 < 100ms
- **TTL 過期**：默認 3600 秒後快取過期，下次請求重新爬取
- **跳過快取**：使用 `force_refresh=true` 強制重新爬取
- **Partial 不快取**：`partial=true` 的結果永不被快取

## 手動驗證建議

- 使用有效 playlist 驗證至少 80% 曲目取得 `title` 與 `video_id`
- 嘗試私密或不存在的 playlist，確認 403/404/410 分類正確
- 連續呼叫相同 playlist：第二次應命中快取且延遲明顯降低；若 `partial=true` 則不應快取
- 測試大列表（>1000 曲）確保在超時前返回 partial=true 而非阻塞
- 驗證所有 error_code 並檢查 trace_id 可用性
