# data-model.md（Phase 1）

## 實體

### Playlist

- playlist_id（string, 必填）：從 URL `list` 參數解析出的 ID，字元限制 34。
- url（string, 必填）：原始播放列表 URL，需含 `list=`。
- title（string, 選填）：播放列表標題，爬取失敗時可為 null。
- video_count（integer, 選填）：預估曲目數量，若無法取得則回傳已解析數量。
- partial（boolean, 必填）：若因超時或缺少 continuation 無法完整取回全部曲目，標記為 true。
- fetched_at（datetime, 選填）：爬取完成時間，便於日後除錯與快取觀察。

### Track

- video_id（string, 必填）：YouTube 影片 ID。
- title（string, 必填）：歌曲/影片標題。
- channel（string, 選填）：頻道或藝人名稱。
- channel_url（string, 選填）：頻道連結。
- url（string, 必填）：影片 URL，由 video_id 組成。
- publish_date（string, 選填）：發布時間（相對時間字串，如 "2 years ago"，保持原樣）。
- duration（string, 選填）：影片長度（如 "3:45"），若無則 null。
- view_count（integer, 選填）：觀看次數，解析失敗則 null。
- position（integer, 選填）：在播放列表中的順序。

### CacheEntry

- key（string, 必填）：`playlist:{playlist_id}`，避免與搜尋快取衝突。
- ttl_seconds（integer, 必填）：取自環境變數 `REDIS_TTL_SECONDS`，預設 3600。
- payload（Playlist, 必填）：完整播放列表資料；partial=true 時不得寫入快取。

## 關聯

- Playlist 1 - N Track：`playlist_id` 對應 tracks 陣列內的所有曲目。
- CacheEntry 與 Playlist 為 1 - 1：快取內容即序列化後的 Playlist 結構。

## 驗證規則

- playlist_url 必須包含 `list` 參數且為 <https://www.youtube.com/> 或 <https://youtu.be/> 網域，否則 400。
- playlist_id 僅接受英數與 `_`/`-`，長度上限 50，否則 400。
- 若 YouTube 回應 403/404/410，對應回傳同碼並附錯誤訊息；其他上游錯誤回傳 502。
- 成功回應需確保 tracks 至少包含 `title` 與 `video_id`，否則視為解析失敗（502）。
- 大型播放列表需迭代 continuation；超時或缺少 token 時回傳 partial=true 並記錄 warning log。
