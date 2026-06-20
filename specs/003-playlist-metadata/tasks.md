---
description: "YouTube 播放列表元數據功能任務清單"
---

# Tasks: YouTube 播放列表元數據提取

**Input**: `/specs/003-playlist-metadata/` 內的 plan/spec/research/data-model/contracts
**Prerequisites**: plan.md（必要）、spec.md（必要）、research.md、data-model.md、contracts/
**Language**: 本文件及相關 `/speckit` 產出須使用正體中文
**Tests**: 憲章允許最小化測試；僅安排必要 smoke 驗證
**Organization**: 依用戶故事分相位，確保可獨立實作與驗證

## 格式: `[ID] [P?] [Story] Description`

- **[P]**: 可平行處理（不同檔案且無相依）
- **[Story]**: 對應用戶故事 (US1...)
- 需列出精確檔案路徑

---

## Phase 1: Setup（共用環境準備）

- [X] T001 確認 `pyproject.toml` 依賴與 Python 3.12 環境已同步（uv sync）
- [X] T002 檢查 `.env` Redis 參數與 `REDIS_TTL_SECONDS` 是否設置（預設 3600）
- [X] T003 [P] 建立新端點使用的 router 檔案骨架 `src/youtube_search/api/v1/playlist.py`

---

## Phase 2: Foundational（阻擋性前置）

- [X] T004 [P] 建立 Playlist/Track Pydantic 模型檔 `src/youtube_search/models/playlist.py` 對應 data-model.md 欄位
- [X] T005 [P] 新增 playlist URL/ID 驗證工具函式至 `src/youtube_search/utils/validators.py`
- [X] T006 將 playlist 路由註冊進 FastAPI 應用 `main.py`（預留引用 `playlist.py` router）

---

## Phase 3: User Story 5 - HTML 解析可行性驗證 (Priority: POC)

**Goal**: 完成 playlist HTML/ytInitialData + continuation 的可行性驗證
**Independent Test**: 使用真實 playlist URL 取得 ≥80% `title` 與 ≥70% 可選欄位，記錄成功率

- [X] T007 [P] [US5] 編寫 POC 腳本 `scripts/playlist_poc.py` 以 requests 取得 playlist HTML 並解析 ytInitialData/continuation
- [X] T008 [US5] 在 `scripts/playlist_poc.py` 輸出提取成功率與樣本數到 `logs/playlist_poc.log`
- [X] T009 [US5] 將 POC 結果與限制更新到 `specs/003-playlist-metadata/research.md`

---

## Phase 4: User Story 1 - 播放列表 URL 解析與驗證 (Priority: P1) 🎯 MVP

**Goal**: 驗證 playlist URL/ID 並回傳基本資訊
**Independent Test**: 呼叫新端點輸入含 `list=` 的 URL，200 回應帶 playlist_id；無效 URL 回 400；不存在回 404；私密/受限回 403；已刪除回 410

- [X] T010 [P] [US1] 在 `src/youtube_search/utils/validators.py` 實作 playlist_url 解析與 playlist_id 驗證（含網域與長度檢查）
- [X] T011 [P] [US1] 擴充 `src/youtube_search/utils/errors.py` 定義 400/403/404/410/502 專用錯誤類型與訊息，並定義結構化錯誤 payload schema（code/message/reason/trace_id/playlist_id/status）；同步更新 `specs/003-playlist-metadata/contracts/openapi.yaml` 錯誤 schema
- [X] T012 [US1] 實作基礎 PlaylistService（僅解析/驗證，不含曲目爬取）於 `src/youtube_search/services/playlist.py`
- [X] T013 [US1] 在 `src/youtube_search/api/v1/playlist.py` 建立 GET `/api/v1/playlist/metadata` 回傳 playlist_id/title/video_count 基本欄位並串接 PlaylistService
- [X] T014 [US1] 強化驗證/錯誤對應：在 `src/youtube_search/api/v1/playlist.py` 將驗證例外對應 400/403/404/410 回應格式，引用 T011 定義的錯誤 schema

---

## Phase 5: User Story 2 - 播放列表歌曲元數據提取 (Priority: P1)

**Goal**: 透過網頁爬取取得全數曲目 metadata（title 必填）並一次性返回
**Independent Test**: 呼叫端點回傳 tracks[]，至少 80% 曲目含 title+video_id，可選欄位盡量填充；不支援分頁

- [X] T014a [P] [US2] 定義超長列表處理策略：在 `src/youtube_search/services/playlist_scraper.py` 設定 continuation 批次上限（建議 15 批）與總超時（30 秒），超過時中止並標記 partial；更新 `specs/003-playlist-metadata/quickstart.md` 說明 partial 行為與 `contracts/openapi.yaml` 補充 partial 欄位
- [X] T015 [P] [US2] 新增 playlist 爬蟲 `src/youtube_search/services/playlist_scraper.py` 解析 ytInitialData 並迭代 continuation token 取得所有曲目
- [X] T016 [P] [US2] 擴充 `src/youtube_search/services/normalizer.py` 將抓取結果正規化為 Track（title/video_id 必填，channel/url/publish_date/duration/view_count/position 選填）
- [X] T017 [US2] 在 `src/youtube_search/services/playlist.py` 整合爬蟲與 normalizer，生成 Playlist 模型並處理 partial 標記（超時或缺 token 時）
- [X] T018 [US2] 更新 `src/youtube_search/api/v1/playlist.py` 回傳完整 tracks[]、partial/fetched_at/video_count 欄位，維持一次性回傳

---

## Phase 6: User Story 3 - 網頁爬取與成本優化 (Priority: P1)

**Goal**: 確保完全採用網頁爬取且具容錯，無任何 YouTube Data API 呼叫
**Independent Test**: 監控請求僅指向 youtube.com 頁面，無 googleapis.com；爬取異常時提供清晰 502 訊息

- [X] T019 [US3] 在 `src/youtube_search/services/playlist_scraper.py` 強制使用 youtube.com/ytInitialData 請求（設定 UA、timeout、禁止 googleapis 網域）
- [X] T020 [P] [US3] 加入可觀測性：於 `src/youtube_search/services/playlist.py` 對爬取/解析錯誤寫入結構化日誌（event/playlist_id/stage/error_code/latency_ms/continuation_count/partial）並包裝為 502 錯誤，引用 T011 定義的錯誤格式

---

## Phase 7: User Story 4 - 播放列表緩存與性能優化 (Priority: P2)

**Goal**: 快取 playlist 結果減少重複爬取，支援 TTL 與 force_refresh
**Independent Test**: 同一 playlist 連續查詢，第二次命中快取延遲顯著降低；TTL 過期後重新爬取；partial 結果不應被快取

- [X] T021 [P] [US4] 在 `src/youtube_search/services/playlist.py` 加入 Redis 快取邏輯（key `playlist:{playlist_id}`，TTL 取自 `REDIS_TTL_SECONDS`，partial 結果不寫入）
- [X] T022 [US4] 於 `src/youtube_search/api/v1/playlist.py` 支援 `force_refresh` 參數並傳遞至 PlaylistService
- [X] T023 [P] [US4] 在 `tests/integration/test_cache.py` 新增播放列表快取命中/過期的 smoke 測試

---

## Phase 8: Polish & Cross-Cutting Concerns

- [x] T024 [P] 更新 `specs/003-playlist-metadata/contracts/openapi.yaml` 以反映最終欄位/錯誤碼（包含 partial 與 force_refresh），確保錯誤 schema 符合 T011 定義
- [x] T025 [P] 補充 `specs/003-playlist-metadata/quickstart.md` 驗證步驟與範例回應（含 partial/force_refresh 情境）
- [x] T026 執行手動驗證並將結果記錄於 `logs/manual-playlist-validation.md`（含 400/403/404/410/502 與快取行為）
- [x] T027 [P] 性能與併發驗證：編寫壓測腳本或手動記錄 50 首播放列表端到端耗時、快取命中延遲、100 併發請求表現，記錄結果於 `logs/perf-playlist.md`；若未達 SC-007/SC-008/SC-010 目標值需記錄實際值與偏差原因

---

## 依賴與執行順序

- 相位順序：Setup → Foundational → US5 (POC) → US1 → US2 → US3 → US4 → Polish
- Phase 2 完成前不得開始任何用戶故事；US5 完成後若結果顯示不可行，須先修正解析策略再進入 US1
- US1 為 MVP 入口，US2/US3 可在 US1 完成後並行；US4 需依賴 US2/US3 產生的結果結構

## 平行處理示例

- US1：T010 與 T011 可平行，T012 之後串接 T013/T014
- US2：T014a 前置，T015 與 T016 可平行，T017 依賴兩者完成後進行，T018 依賴 T017
- US4：T021 可與 T023 並行；T022 依賴 T021 介面
- Phase 8：T024/T025/T027 可平行，T026 依賴前述階段完成

## 實作策略

- MVP 先行：完成 US1（URL 驗證與基本回應）即可交付初版並進行手動驗證
- 逐步增量：依序完成 US2（曲目提取）、US3（反 Data API 防護與容錯）、US4（快取優化），每階段皆可獨立驗證
- 若 POC（US5）顯示解析成功率不足，先修正爬蟲策略再繼續後續故事
