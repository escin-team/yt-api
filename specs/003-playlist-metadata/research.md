# research.md（Phase 0）

## 決策與結論

### 1) 播放列表頁面解析策略

- Decision: 使用 playlist HTML 中的 `ytInitialData` 解析初始批次，並透過 `continuation` token 迭代抓取後續批次；維持 `requests + json`，暫不新增額外解析套件。
- Rationale: 與既有搜尋爬蟲一致（同樣依賴 ytInitialData），不需新依賴即可取得列表項目與 `continuation`; 透過 token 逐批拉取可覆蓋長列表且成本最低。
- Alternatives considered:
  - 直接解析純 HTML DOM：結構脆弱且難以處理分頁/懸浮載入；
  - 借用非官方 YouTube API 套件：引入額外依賴與合規風險，且不保證穩定。

### 2) 長列表（>1000 首）處理方式

- Decision: 迭代 `continuation`，設定最大批次與超時（例如 30 秒）避免阻塞；若超過時間或無 token，回傳已取得的部分並標記 `partial=true`，同時記錄告警 log。
- Rationale: 可在保持一次性回傳的前提下提供最佳努力；時間界線避免極端列表造成阻塞；partial 標記讓用戶可見。
- Alternatives considered:
  - 強制分頁：違反一次性回傳需求；
  - 直接拒絕長列表：使用者體驗差，且無法完成 POC 成功標準。

### 3) 緩存與過期策略

- Decision: 播放列表結果以 playlist ID 為 key 進行 Redis set/get，TTL 取 `REDIS_TTL_SECONDS`（預設 3600 秒）；當 partial=true 或爬取錯誤時不寫入快取，避免污染。
- Rationale: 與現有搜尋快取方式一致，降低重複爬取成本；跳過失敗結果可確保後續重試。
- Alternatives considered:
  - 以 URL 為 key：URL 參數順序可能不同，易產生重複快取；
  - 永不快取：會大幅增加爬取成本與延遲。

### 4) 錯誤分類與回應

- Decision: URL 格式驗證失敗回傳 400；playlist 不存在/已刪除回 404；私密/受限回 403；明確標記已刪除情境回 410；其他爬取或解析失敗回 502 並附錯誤訊息。
- Rationale: 與功能規範一致並提供清晰診斷；502 用於上游不可用（YouTube 變更或暫時故障）。
- Alternatives considered:
  - 以單一 500 處理：訊息不夠明確，無法對症處理；
  - 以 200 + 錯誤碼包在 payload：違反 REST 慣例且不利客戶端處理。

## 待辦與依賴處理

- NEEDS CLARIFICATION 項目已解決：
  - 播放列表解析方式：採用 ytInitialData + continuation，無需新增套件。
  - 大型列表處理：設定批次迭代與超時，必要時回傳 partial。
- 無新增外部依賴；沿用 requests/anyio/redis。
- 後續設計需在 data-model/contract 反映 `partial` 旗標與 continuation 迭代邏輯的限制說明。

## POC 驗證結果（2025-12-08）

- 腳本：`scripts/playlist_poc.py`（輸出至 `logs/playlist_poc.log`，依 tasks T007-T009）。
- 樣本 1：`PLFgquLnL59alGJcdc0BEZJb2p7IgkTM5u`（官方精選）
  - 取得 0 首、未進入 continuation（耗時 158ms）；推測為混合/個人化清單結構，ytInitialData 無 `playlistVideoRenderer`。
- 樣本 2：`PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU`（Python 教學）
  - `track_count=100`、`title_coverage=100%`、`duration/position=100%`，`channel/channel_url/publish_date/view_count=0%`，continuation 請求 2 次，耗時約 525ms，partial=false。
- 見解：
  - 標準 playlist 可透過 ytInitialData + continuation 拿到完整 title/video_id；需補強 shortBylineText/metadata 解析才能填滿 channel/view_count 等可選欄位。
  - 混合/推薦類 playlist（可能使用 playlistPanelVideoRenderer）需額外邏輯或列為已知限制，避免 0 结果情境。

## 實現配置（Phase 2 - T014a）

### 超長列表處理參數

為避免極端情況下的無限等待與資源耗盡，採用下列參數：

- **continuation 批次上限**：15 批
  - 每批通常包含 ~100 條項目（依 YouTube 動態調整）
  - 15 批約可涵蓋 1500+ 項目
  - 超過 15 批時標記 `partial=true` 並停止迭代

- **總爬取超時**：30 秒
  - 初始 URL 請求：最多 10 秒
  - 每個 continuation 請求：最多 5 秒
  - 若超過 30 秒門檻，立即停止並標記 `partial=true`，回傳已獲得的項目

- **partial 標記與緩存規則**：
  - 當 `partial=true` 時，**不將結果寫入 Redis 快取**
  - 下次請求該 playlist 時強制重試（cache miss）
  - 已成功取得的完整清單（partial=false）才寫入快取，TTL 遵循 `REDIS_TTL_SECONDS`

- **錯誤日誌紀錄**：
  - 當觸發超時或缺少 continuation 時，記錄 warning 級別日誌
  - 日誌包含：playlist_id、stage（initial / continuation N），error_code（TIMEOUT / NO_CONTINUATION），latency_ms，fetched_count，partial flag
