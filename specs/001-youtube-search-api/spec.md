# 功能規範：YouTube 搜尋 API

**功能分支**：`001-youtube-search-api`
**建立日期**：2025-12-06
**狀態**：已完成
**輸入**：使用者描述：使用 YouTube search URL 建立 API 功能，輸入關鍵字找出符合的影片，並提取出其中的 metadata（如 video_id），以便後續其他系統使用

**語言**：本文件及所有 `/speckit` 產出必須使用正體中文撰寫

## 用戶情景與測試 *(必須)*

### 用戶故事 1 - 基本搜尋功能（優先級：P1）

系統提供 API 端點接受關鍵字輸入，透過 YouTube 搜尋結果頁面取得符合的影片清單。

**為何此優先級**：這是核心功能，沒有它其他功能無法運作。系統能否從 YouTube 取得搜尋結果是整個功能的基礎。

**獨立測試**：可直接呼叫 API 端點傳入單一關鍵字（例如「Python 教學」），驗證是否返回含有影片資訊的 JSON 回應，並且至少包含 video_id 欄位。

**接受情景**：

1. **當** 客戶端呼叫 `GET /api/v1/search?keyword=Python教學` **則** 系統返回 HTTP 200 且包含影片清單
2. **當** 清單中至少有一筆記錄 **則** 該記錄需包含 `video_id`、`title`、`url` 等基本 metadata
3. **當** 搜尋無結果 **則** 系統返回空清單，而非錯誤
4. **當** YouTube 連線失敗 **則** 系統返回 HTTP 503 Service Unavailable

---

### 用戶故事 2 - 元數據提取（優先級：P1）

API 從搜尋結果中提取並整理各影片的 metadata，包括 video_id、標題、描述、頻道、發佈日期等，以標準化格式返回。

**為何此優先級**：提取 metadata 是核心價值主張。無法有效提取 metadata 就無法滿足「供後續系統使用」的需求。

**獨立測試**：搜尋後檢查回應中的每筆影片記錄都包含預期的 metadata 欄位（video_id、title、channel、publish_date 等），且資料格式一致。可選欄位（title、channel、publish_date、view_count、description）提取成功率應 ≥ 50%。

**接受情景**：

1. **當** 搜尋返回結果 **則** 每筆影片至少包含 `video_id`、`title`、`channel`、`url`
2. **當** metadata 有可用的發佈日期 **則** 應包含 `publish_date` 欄位
3. **當** metadata 有觀看計數 **則** 應包含 `view_count` 欄位（若可取得）

---

### 用戶故事 3 - 結果排序與過濾（優先級：P2）

API 支援根據相關性、發佈日期或觀看數對結果進行排序，允許客戶端指定返回的影片數量上限。

**為何此優先級**：提升結果品質與靈活性。P1 功能達成後，P2 優化搜尋體驗與效率。

**獨立測試**：傳入 `sort_by=relevance&limit=5` 參數，驗證是否返回最多 5 筆記錄且按相關性排序。

**接受情景**：

1. **當** 未指定 `limit` 參數 **則** 預設返回 1 筆結果（相關性最高的影片）
2. **當** 指定 `limit=5` **則** 返回最多 5 筆結果
3. **當** 指定 `sort_by=relevance` **則** 結果按相關性排序（預設行為）
4. **當** 指定 `sort_by=date` **則** 結果按發佈日期新舊排序

---

### 邊界情況

- 搜尋關鍵字為空或僅空白時如何處理？
- 搜尋關鍵字包含特殊字元或 Unicode 時是否正確編碼？
- YouTube 回應逾時或無法連接時系統如何回應？
- 同一關鍵字頻繁搜尋是否需要快取或速率限制？

## 需求 *(必須)*

### 功能性需求

- **FR-001**：系統必須透過公開可存取的 YouTube 搜尋 URL（`https://www.youtube.com/results?search_query={keyword}`）取得搜尋結果
- **FR-002**：系統必須從搜尋結果中正確提取 `video_id`
- **FR-003**：系統必須提供 RESTful API 端點接受關鍵字參數並返回 JSON 格式結果
- **FR-004**：系統必須為每筆影片至少提取 `video_id`、`title`、`channel`、`url` 等 metadata
- **FR-005**：系統必須驗證輸入關鍵字非空且長度為 1-200 字元。關鍵字在驗證前執行 trim（去除首尾空白），trim 後若為空則返回 HTTP 400 Bad Request
- **FR-006**：系統必須記錄所有搜尋請求與錯誤到結構化日誌中
- **FR-007**：系統必須遵守 YouTube 服務條款，不下載或儲存媒體內容，僅提取 metadata
- **FR-008**：系統必須實現搜尋結果快取機制，同一關鍵字的搜尋結果 TTL 為 1 小時。快取後端使用 Redis，連線參數透過環境變數配置（`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`）
- **FR-009**：系統必須支援 `limit` 查詢參數指定返回結果數量，預設值為 1，允許值為 1-100，超過上限則返回 HTTP 400 Bad Request
- **FR-010**：系統必須採用 RESTful API 回應格式標準。成功回應（HTTP 200）返回搜尋結果 data；失敗回應返回對應 HTTP 狀態碼（400、503 等）+ JSON 錯誤對象 `{ error: string, error_code: string }`。錯誤碼包含：`MISSING_PARAMETER`、`INVALID_KEYWORD_LENGTH`、`INVALID_LIMIT`、`YOUTUBE_UNAVAILABLE`、`CACHE_UNAVAILABLE`、`INTERNAL_ERROR`

### 主要實體

- **搜尋結果（SearchResult）**：代表一次搜尋操作的結果集合
  - `search_keyword`：搜尋關鍵字
  - `result_count`：返回的影片數量
  - `videos`：影片清單（Video 實體的陣列）
  - `timestamp`：搜尋時間戳記

- **影片（Video）**：代表單個 YouTube 影片的 metadata
  - `video_id`：YouTube 影片唯一識別碼（**必須**，提取失敗時該筆影片不返回）
  - `title`：影片標題（最佳努力，無法提取時設為 null）
  - `url`：影片完整 URL（最佳努力，無法提取時設為 null）
  - `channel`：頻道名稱（最佳努力，無法提取時設為 null）
  - `channel_url`：頻道 URL（最佳努力，無法提取時設為 null）
  - `publish_date`：發佈日期（最佳努力，無法提取時設為 null）
  - `view_count`：觀看次數（最佳努力，無法提取時設為 null）
  - `description`：影片描述摘要（最佳努力，無法提取時設為 null）

## 成功標準 *(必須)*

### 可測量的成果

- **SC-001**：API 在收到有效的關鍵字搜尋請求後，3 秒內返回結果（包括網路延遲）
- **SC-002**：搜尋結果中的 video_id 提取正確率達 95% 以上（可手動驗證前 10 筆結果對比 YouTube 頁面）
- **SC-003**：API 處理 100 個不同的測試關鍵字，至少 90% 無錯誤返回結果
- **SC-004**：metadata 欄位一致性達 100%（每筆結果都包含預期的必須欄位）
- **SC-005**：系統能正確處理特殊字元、Unicode、空格等邊界情況，不拋出未預期的異常
- **SC-006**：後續系統能直接使用返回的 video_id 識別或存取影片資訊

## 假設與限制

- 使用直接爬蟲 YouTube 搜尋頁面（而非官方 API）實現以避免 API 成本，因此可能受 HTML 結構變化影響
- YouTube 搜尋 URL (`https://www.youtube.com/results?search_query={keyword}`) 返回 HTML 內容，需進一步解析以提取影片資訊
- 爬蟲需識別 HTML 中的 `var ytInitialData = {...}` JSON 結構，提取邏輯必須針對目前的 YouTube 頁面結構
- 不使用官方 YouTube Data API，避免 API 配額限制但需承擔頁面結構變化風險
- POC 階段優先考慮功能可用性，而非大規模併發支援
- 搜尋結果排序基於 YouTube 頁面的預設順序（相關性）
- YouTube 連線故障（逾時、無法連接）時立即返回 HTTP 503 Service Unavailable，不自動重試，由客戶端決定是否稍後重新請求
- 快取實現：同一關鍵字搜尋結果在 Redis 中快取 1 小時（TTL 3600 秒）。超過 TTL 後自動重新爬蟲。快取鍵格式為 `youtube_search:{keyword_hash}`
- Redis 連線參數由環境變數提供：`REDIS_HOST`（預設 localhost）、`REDIS_PORT`（預設 6379）、`REDIS_DB`（預設 0）
- Redis 連線失敗時：系統拋出例外，API 返回 HTTP 503 Service Unavailable，error_code=CACHE_UNAVAILABLE，error 訊息說明快取服務不可用。系統不回退到無快取模式，要求 Redis 必須可用才能提供服務
- Metadata 提取策略：`video_id` 為必須欄位，無法提取則該筆影片整個不返回；其他欄位（title、channel、publish_date、view_count 等）採用最佳努力提取，無法取得時設為 null，不影響整筆影片返回
- API 回應格式遵循 RESTful 標準：成功回應（HTTP 200）直接返回 SearchResult 對象；失敗回應返回對應 HTTP 狀態碼及錯誤 JSON 對象 `{ error: "string", error_code: "string" }`。常見錯誤狀態碼包括 400（參數驗證失敗）、503（YouTube 連線故障）等

## 澄清

### Session 2025-12-07

- Q: YouTube 連線故障（逾時、無法連接）時系統應如何回應？ → A: 立即返回 HTTP 503 Service Unavailable，不重試
- Q: 同一關鍵字頻繁搜尋是否需要快取或速率限制？ → A: 實現 1 小時快取（Redis），無速率限制（POC 階段）
- Q: publish_date 與 view_count 無法提取時應如何處理？ → A: 最佳努力提取，無法取得時設為 null；video_id 為必須，無法提取則該筆影片整個不返回
- Q: 搜尋結果數量限制如何設定？ → A: 預設返回 1 筆，支援 limit 參數（1-100），超過則返回 HTTP 400
- Q: API 回應格式標準為何？ → A: RESTful 格式，成功返回 HTTP 200 + data，失敗返回 HTTP 狀態碼 + { error, error_code }

## POC 驗證

### 目標

驗證使用 YouTube 搜尋 URL 直接爬蟲的可行性，確認能否正確提取影片 metadata。

### 驗證方式

- **測試關鍵字**：「張學友 吻別」
- **測試方法**：
  1. 發送 HTTP GET 請求至 `https://www.youtube.com/results?search_query=張學友 吻別`
  2. 從返回的 HTML 中提取 `var ytInitialData = {...}` JSON 字串
  3. 解析 JSON 提取影片列表中的 video_id、title、channel 等欄位
  4. 驗證提取結果與 YouTube 頁面顯示內容相符

### 驗證結果 ✅ 成功

**環境**：macOS，Python 3，使用 urllib + json + regex

**結果摘要**：

- ✅ 成功取得 YouTube 搜尋結果頁面（HTML，大小 ~1.2MB）
- ✅ 成功提取 `var ytInitialData` JSON 結構（大小 ~550KB）
- ✅ 成功解析 JSON 並提取 22 個影片記錄
- ✅ 正確提取所有必要 metadata：video_id、title、channel

**實際提取樣本**（前 3 筆）：

| # | video_id | title | channel |
|---|----------|-------|---------|
| 1 | mIF-nn_y2_8 | 張學友 Jacky Cheung - 吻別 | 音樂無疆界 Music Without Boundaries |
| 2 | k6zmy0yvXB4 | 張學友   吻別 無損音樂FLAC 歌詞LYRICS 純享 | MusicDelta |
| 3 | ZRCr3sqePzg | 1993 張學友《吻別》MV 香港完整版 ft. 周海媚 | 張哲生 |

### 驗證標準

✅ **可行**：成功提取正確的 video_id 與基本 metadata（title、channel）

### 技術實現細節確認

- **HTTP 請求**：使用標準 urllib，需設定 User-Agent 表頭避免被擋
- **HTML 解析**：使用正則表達式提取 `var ytInitialData = (...);` JSON 字串
- **JSON 解析**：標準 json 庫解析結構

**JSON 結構路徑**：

```
data['contents']['twoColumnSearchResultsRenderer']['primaryContents']
    ['sectionListRenderer']['contents'][...]['itemSectionRenderer']
    ['contents'][...]['videoRenderer']
```

**Metadata 提取路徑**：

- `video_id`：直接字段
- `title`：`title.runs[0].text`
- `channel`：`longBylineText.runs[0].text`

### 後續行動

✅ **驗證成功** → 進入 `/speckit.plan` 階段進行技術設計

**建議工具組**：

- `requests`：HTTP 請求
- `re`：正則表達式提取
- `json`：JSON 解析
- （可選）`BeautifulSoup`：HTML 更結構化解析
