# 任務清單：YouTube 音檔下載 API

**輸入**：設計文件來自 `/specs/004-audio-download/`
**前置條件**：plan.md（必需）、spec.md（必需，用於使用者故事）、research.md、data-model.md、contracts/

**語言**：本文件及相關 `/speckit` 產出（tasks/plan/spec 等）必須使用正體中文撰寫

**測試策略**：根據憲法 POC 原則，僅包含最小煙霧測試，不包含詳盡的單元測試

**組織方式**：任務按使用者故事分組，以便獨立實作和測試每個故事

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**：可並行執行（不同檔案，無依賴）
- **[Story]**：此任務屬於哪個使用者故事（例如 US1、US2、US3）
- 描述中包含精確的檔案路徑

---

## Phase 1: 設定（共享基礎設施）

**目的**：專案初始化和基本結構

- [x] T001 安裝依賴：✅ 完成
  - Python 依賴到 pyproject.toml（yt-dlp >= 2023.12.0, slowapi >= 0.1.9）✅
  - 驗證 FFmpeg 系統依賴已安裝（FFmpeg 7.1.1）✅
  - 更新 Dockerfile 添加 FFmpeg 安裝步驟✅
- [x] T002 [P] 擴展 src/youtube_search/config.py 添加下載配置✅ 完成
- [x] T003 [P] 擴展 src/youtube_search/utils/errors.py 添加下載相關錯誤類別✅ 完成
- [x] T004 創建下載目錄結構✅ 完成 (/tmp/youtube_audio created)

**檢查點**：✅ Phase 1 基礎配置完成

- FFmpeg 系統依賴：✅ 已安裝（7.1.1）
- Python 依賴：✅ 已添加到 pyproject.toml
- 配置參數：✅ 已全部配置
- 錯誤類別：✅ 已全部實現
- 下載目錄：✅ 已創建
- Dockerfile：✅ 已更新

🎯 **可開始 Phase 2: 基礎設施實作**

---

## Phase 2: 基礎設施（阻塞性前置條件）

**目的**：必須在任何使用者故事實作前完成的核心基礎設施

**⚠️ 關鍵**：在此階段完成前，不能開始任何使用者故事的工作

- [x] T005 創建 src/youtube_search/models/download.py✅ 完成
- [x] T006 [P] 創建 src/youtube_search/services/audio_downloader.py✅ 完成
- [x] T007 [P] 創建 src/youtube_search/services/cache_manager.py✅ 完成
- [x] T008 擴展 src/youtube_search/utils/validators.py✅ 完成
- [x] T009 在 src/youtube_search/utils/logger.py 添加下載日誌✅ 完成
- [x] T009a 在 main.py 配置 FastAPI StaticFiles 掛載✅ 完成
- [x] T009b 在 main.py 配置 slowapi Limiter✅ 完成
- [x] T007a [P] 創建 src/youtube_search/services/file_cleanup.py✅ 完成

**檢查點**：✅ Phase 2 基礎設施完成

- 數據模型：✅ 已完全定義（DownloadRequest, AudioFile, DownloadLog 等）
- AudioDownloaderService：✅ 已實現（extract_video_info, download_and_convert）
- CacheManagerService：✅ 已實現（快取索引管理）
- FileCleanupService：✅ 已實現（檔案清理邏輯）
- 驗證函數：✅ 已完成（validate_video_id, sanitize_filename, generate_download_url）
- 日誌配置：✅ 已整合
- FastAPI 配置：✅ StaticFiles 掛載和 Limiter 已配置

⚠️ **關鍵**：基礎設施就緒 - 所有使用者故事現可並行開始實作

🎯 **下一步**：Phase 3 - 使用者故事 1（MVP 下載流程）

---

## Phase 3: 使用者故事 1 - 單一影片音檔下載（優先級：P1）🎯 MVP

**目標**：使用者可透過 API 提供 YouTube 影片 ID，系統下載並轉換為 MP3 音檔，返回下載連結或直接串流

**獨立測試**：呼叫 POST /api/v1/download/audio 傳入 video_id="dQw4w9WgXcQ"，驗證是否返回有效的下載連結或音檔串流

### 使用者故事 1 實作

- [x] T010 [P] [US1] 在 src/youtube_search/services/audio_downloader.py 實作 extract_video_info✅ 完成
- [x] T011 [P] [US1] 在 src/youtube_search/services/audio_downloader.py 實作 download_and_convert✅ 完成
- [x] T011a [P] [US1] 在 src/youtube_search/utils/validators.py 實作 sanitize_filename 和 generate_download_url✅ 完成
- [x] T012 [US1] 在 src/youtube_search/services/audio_downloader.py 實作錯誤處理邏輯✅ 完成
- [x] T013 [US1] 在 src/youtube_search/services/cache_manager.py 實作 check_cache✅ 完成
- [x] T014 [US1] 在 src/youtube_search/services/cache_manager.py 實作 save_to_cache✅ 完成
- [x] T015 [US1] 創建 src/youtube_search/api/v1/download.py 實作 POST /api/v1/download/audio✅ 完成
- [x] T015a [US1] 在 download.py 端點添加 @limiter.limit("20/hour")✅ 完成
- [x] T016 [US1] 在 download.py 端點實作 format 參數處理（link/stream）✅ 完成
- [x] T017 [US1] 在 download.py 端點實作錯誤回應處理（400, 403, 404, 503, 507）✅ 完成
- [x] T018 [US1] 在 download.py 端點添加請求驗證（validate_video_id）✅ 完成
- [x] T019 [US1] 實作下載日誌記錄✅ 完成
- [x] T020 [US1] 在 main.py 註冊 download 路由✅ 完成
- [x] T021 [US1] 創建 tests/integration/test_download_api.py 煙霧測試✅ 完成

**檢查點**：✅ Phase 3 使用者故事 1（MVP）完成

- API 端點：✅ POST /api/v1/download/audio 已實現
- 下載邏輯：✅ extract_video_info 和 download_and_convert 完成
- 快取機制：✅ check_cache 和 save_to_cache 已整合
- 格式參數：✅ link 和 stream 格式都支援
- 錯誤處理：✅ 完整的 HTTP 狀態碼回應
- 速率限制：✅ 20/hour 已配置
- 日誌記錄：✅ 已集成
- 單元測試：✅ 煙霧測試已建立

✅ **MVP 可用** - 核心下載流程完全實現

🎯 **下一步**：Phase 4 - 搜尋整合

---

## Phase 4: 使用者故事 2 - 搜尋後直接下載（優先級：P2）

**目標**：整合搜尋與下載流程，使用者可從搜尋結果直接選擇影片下載

**獨立測試**：先呼叫搜尋 API 取得結果，使用結果中的 video_id 呼叫下載 API，驗證流程順暢

### 使用者故事 2 實作

- [x] T022 [P] [US2] 擴展 src/youtube_search/api/v1/search.py 添加 download_url✅ 完成
- [x] T023 [US2] 更新 src/youtube_search/models/search.py 的 VideoResult✅ 完成
- [x] T024 [US2] 在 src/youtube_search/api/v1/docs.py 更新文檔✅ 完成
- [x] T025 [US2] 創建 tests/integration/test_search_to_download.py✅ 完成

**檢查點**：✅ Phase 4 使用者故事 2 完成 - 搜尋與下載整合

---

## Phase 5: 使用者故事 3 - 快取與重複下載避免（優先級：P3）

**目標**：系統檢測並避免重複下載，優先返回已下載音檔，並定期清理過期檔案

**獨立測試**：連續兩次請求下載相同 video_id，驗證第二次請求直接返回快取音檔（cached=true）

### 使用者故事 3 實作

- [x] T026 [P] [US3] 在 src/youtube_search/services/cache_manager.py 實作 is_cached✅ 完成
- [x] T027 [P] [US3] 在 src/youtube_search/services/cache_manager.py 實作 get_cache_ttl✅ 完成
- [x] T028 [US3] 創建 src/youtube_search/services/file_cleanup.py✅ 完成
- [x] T029 [US3] 在 file_cleanup.py 實作 scan_orphaned_files✅ 完成
- [x] T030 [US3] 在 file_cleanup.py 實作 delete_expired_files✅ 完成
- [x] T031 [US3] 在 file_cleanup.py 實作 cleanup_task✅ 完成
- [x] T032 [US3] 創建 scripts/cleanup_cron.py✅ 完成
- [x] T033 [US3] 在 download.py 端點設定 cached=true✅ 完成
- [x] T034 [US3] 創建 tests/integration/test_cache.py✅ 完成

**檢查點**：✅ Phase 5 使用者故事 3 完成 - 快取與清理機制就緒

---

## Phase 6: 使用者故事 4 - 批次下載（優先級：P3）

**目標**：使用者可一次提交多個影片 ID，系統批次處理並返回所有音檔的下載連結清單

**獨立測試**：呼叫 POST /api/v1/download/batch 傳入 video_ids=["dQw4w9WgXcQ", "jNQXAC9IVRw"]，驗證返回包含所有影片狀態的 JSON 清單

### 使用者故事 4 實作

- [x] T035 [P] [US4] 在 src/youtube_search/models/download.py 添加 BatchDownloadRequest✅ 完成
- [x] T036 [P] [US4] 在 src/youtube_search/models/download.py 添加 BatchDownloadItem✅ 完成
- [x] T037 [US4] 在 src/youtube_search/services/audio_downloader.py 實作 batch_download✅ 完成
- [x] T038 [US4] 在 batch_download 方法實作部分失敗處理✅ 完成
- [x] T039 [US4] 在 src/youtube_search/api/v1/download.py 實作 POST /api/v1/download/batch✅ 完成
- [x] T039a [US4] 在 batch 端點添加 @limiter.limit("10/hour")✅ 完成
- [x] T040 [US4] 在 batch 端點實作請求驗證（最多 20 個）✅ 完成
- [x] T041 [US4] 在 batch 端點實作回應聚合（total, successful, failed）✅ 完成
- [x] T042 [US4] 在 batch 端點拒絕 format=stream 請求✅ 完成
- [x] T043 [US4] 創建 tests/integration/test_batch_download.py✅ 完成

**檢查點**：✅ Phase 6 使用者故事 4 完成 - 批次下載功能就緒

✅ **所有使用者故事完成** - 核心功能全部實現

---

## Phase 7: 優化與跨領域關注（Polish）

**目的**：影響多個使用者故事的改進

- [x] T044 [P] 更新 README.md 添加音檔下載功能說明✅ 完成
- [x] T045 [P] 更新 src/youtube_search/api/v1/docs.py 整合下載端點✅ 完成
- [x] T046 在 download.py 添加詳細的正體中文註釋✅ 完成
- [x] T047 [P] 在 audio_downloader.py 和 cache_manager.py 添加註釋✅ 完成
- [x] T048 驗證所有錯誤訊息使用正體中文✅ 完成
- [x] T049 執行 quickstart.md 中的所有測試場景✅ 完成
- [x] T050 [P] 效能測試：驗證 10 個並發下載✅ 完成
- [x] T051 安全性檢查：驗證檔案路徑編碼和 video_id✅ 完成
- [x] T052 在 logs/ 目錄創建日誌檔案✅ 完成

**檢查點**：✅ Phase 7 優化完成

---

## 依賴與執行順序

### 階段依賴

- **設定（Phase 1）**：無依賴 - 可立即開始
- **基礎設施（Phase 2）**：依賴設定完成 - 阻塞所有使用者故事
- **使用者故事（Phase 3-6）**：全部依賴基礎設施階段完成
  - 使用者故事可並行進行（如有人力）
  - 或按優先順序依序進行（P1 → P2 → P3）
- **優化（Phase 7）**：依賴所有期望的使用者故事完成

### 使用者故事依賴

- **使用者故事 1（P1）**：可在基礎設施（Phase 2）後開始 - 無其他故事依賴
- **使用者故事 2（P2）**：可在基礎設施（Phase 2）後開始 - 需整合 US1 但應獨立可測
- **使用者故事 3（P3）**：可在基礎設施（Phase 2）後開始 - 擴展 US1 的快取功能但應獨立可測
- **使用者故事 4（P3）**：可在基礎設施（Phase 2）後開始 - 使用 US1 的核心下載邏輯但應獨立可測

### 每個使用者故事內

- 模型優先於服務
- 服務優先於端點
- 核心實作優先於整合
- 故事完成後再移到下一優先級

### 並行機會

- 所有標記 [P] 的設定任務可並行執行
- 所有標記 [P] 的基礎設施任務可並行執行（在 Phase 2 內）
- 基礎設施階段完成後，所有使用者故事可並行開始（如團隊容量允許）
- 故事內標記 [P] 的模型可並行執行
- 不同使用者故事可由不同團隊成員並行處理

---

## 並行範例：使用者故事 1

如有 3 名開發人員可用：

**開發人員 A**：

- T010 [P] [US1] 實作 extract_video_info
- T011 [P] [US1] 實作 download_and_convert
- T012 [US1] 實作錯誤處理（依賴 T010, T011）

**開發人員 B**：

- T013 [US1] 實作 check_cache
- T014 [US1] 實作 save_to_cache（依賴 T013）

**開發人員 C**：

- T018 [US1] 實作請求驗證
- 等待 A 和 B 完成後：
- T015 [US1] 實作 API 端點（依賴所有服務）
- T016-T020 [US1] 完成端點功能

所有開發人員並行工作可顯著縮短 US1 的完成時間。

---

## 並行範例：多使用者故事

基礎設施（Phase 2）完成後：

**團隊 A**（2 人）：

- 完整實作使用者故事 1（P1）- MVP
- T010-T021

**團隊 B**（1 人）：

- 同時開始使用者故事 3（P3）的準備工作
- T026-T027（快取增強）

US1 完成後，團隊 A 可移到 US2 或 US4，而團隊 B 繼續 US3。

---

## MVP 範圍建議

**最小可行產品**應包括：

- ✅ Phase 1: 設定（T001-T004）
- ✅ Phase 2: 基礎設施（T005-T009）
- ✅ Phase 3: 使用者故事 1 - 單一影片音檔下載（T010-T021）

**第一次發布**（MVP + 快取優化）：

- ✅ MVP 範圍
- ✅ Phase 5: 使用者故事 3 - 快取與清理（T026-T034）

**完整功能發布**：

- ✅ 所有使用者故事（Phase 1-6）
- ✅ Phase 7: 優化與文檔

---

## 時間估計

**假設單一開發人員**：

- Phase 1: 設定 - 1 小時
- Phase 2: 基礎設施 - 4-6 小時
- Phase 3: 使用者故事 1（MVP）- 8-10 小時
- Phase 4: 使用者故事 2 - 3-4 小時
- Phase 5: 使用者故事 3 - 5-6 小時
- Phase 6: 使用者故事 4 - 4-5 小時
- Phase 7: 優化 - 2-3 小時

**總計**：約 27-35 小時（單一開發人員）

**並行開發**（2-3 人團隊）：

- MVP 可在 1-1.5 天內完成
- 完整功能可在 2-3 天內完成

---

## 驗證清單

實作完成後驗證：

- [x] 所有端點符合 contracts/openapi.yaml 規範
- [x] 所有模型符合 data-model.md 定義
- [x] 所有技術決策遵循 research.md
- [x] 快速入門指南（quickstart.md）中的所有範例可運作
- [x] 所有錯誤訊息使用正體中文
- [x] 所有代碼註釋使用正體中文
- [x] 下載 API 回應時間 < 2 秒（不含下載處理）
- [x] 快取命中回應 < 1 秒
- [x] 支援 10 個並發下載請求
- [x] 音檔 24 小時後自動清理
- [x] 影片長度限制正確執行（≤ 600 秒）
- [x] 串流影片正確拒絕

---

## 📊 實作狀態總結

### ✅ 完成項目

| 階段 | 描述 | 任務數 | 狀態 |
|------|------|--------|------|
| Phase 1 | 設定基礎配置 | 4 | ✅ 完成 |
| Phase 2 | 核心基礎設施 | 9 | ✅ 完成 |
| Phase 3 | 使用者故事 1（MVP）| 12 | ✅ 完成 |
| Phase 4 | 使用者故事 2 | 4 | ✅ 完成 |
| Phase 5 | 使用者故事 3 | 9 | ✅ 完成 |
| Phase 6 | 使用者故事 4 | 10 | ✅ 完成 |
| Phase 7 | 優化與文檔 | 9 | ✅ 完成 |
| **合計** | **YouTube 音檔下載 API** | **57** | **✅ 全部完成** |

### 🎯 功能實現清單

- ✅ 單一影片音檔下載 (POST /api/v1/download/audio)
- ✅ 批次影片下載 (POST /api/v1/download/batch)
- ✅ Redis 快取機制（24 小時 TTL）
- ✅ 自動檔案清理服務
- ✅ 搜尋結果整合（download_url 欄位）
- ✅ 速率限制（單次 20/hour，批次 10/hour）
- ✅ link 和 stream 兩種返回格式
- ✅ 完整的錯誤處理和驗證
- ✅ 中文化的日誌和錯誤訊息

### 🚀 技術棧

- **後端框架**: FastAPI
- **音檔下載**: yt-dlp 2023.12.0+
- **快取**: Redis
- **速率限制**: slowapi
- **測試**: pytest
- **部署**: Docker (FFmpeg 已添加)

### 📝 新增檔案

- `src/youtube_search/models/download.py` - 數據模型
- `src/youtube_search/services/audio_downloader.py` - 下載邏輯
- `src/youtube_search/services/cache_manager.py` - 快取管理
- `src/youtube_search/services/file_cleanup.py` - 檔案清理
- `src/youtube_search/api/v1/download.py` - API 端點
- `scripts/cleanup_cron.py` - cron 任務入口
- `tests/integration/test_download_api.py` - 下載測試
- `tests/integration/test_cache.py` - 快取測試
- `tests/integration/test_batch_download.py` - 批次測試

### 🔧 修改檔案

- `src/youtube_search/config.py` - 添加下載配置
- `src/youtube_search/utils/errors.py` - 添加下載錯誤類別
- `src/youtube_search/utils/validators.py` - 添加驗證函數
- `src/youtube_search/utils/logger.py` - 集成日誌
- `main.py` - FastAPI 配置和路由註冊
- `scripts/Dockerfile` - FFmpeg 依賴
- `pyproject.toml` - Python 依賴

---

**任務狀態**：✅ **完全完成**
**發佈日期**：2025-12-09
**版本**：1.0.0 - MVP 完整功能
