---
description: "MCP 支援功能的任務清單"
feature: "002-mcp-support"
---

# 任務清單：MCP (Model Context Protocol) 支援

**輸入**：設計文件自 `/specs/002-mcp-support/` （plan.md, spec.md）
**前置條件**：plan.md（必須）、spec.md（用戶故事，必須）

**語言**：本文件及相關 `/speckit` 產出（tasks/plan/spec 等）必須使用正體中文撰寫

**測試**：本任務清單包含煙測試和主要錯誤情況測試。根據 MVP 定義（P1 + P2 功能），測試已納入。

**組織**：任務按用戶故事組織，以支持每個故事的獨立實現和測試。

## 格式：`[ID] [P?] [Story?] 描述`

- **[P]**：可並行執行（不同檔案，無相依性）
- **[Story]**：此任務屬於的用戶故事（例如 US1、US2、US3）
- 在描述中包含確切的檔案路徑

## 路徑規約

- **單一專案**：`src/`、`tests/` 在儲存庫根目錄
- 下面的路徑假設單一專案 - 根據 plan.md 結構調整

---

## 第 1 階段：準備（專案初始化）

**目標**：專案結構初始化和基本依賴配置

- [x] T001 根據實現計劃建立 `src/youtube_search/mcp/` 目錄結構
- [x] T002 [P] 在 `pyproject.toml` 中新增 MCP 依賴（mcp>=1.0.0 及相關套件）
- [x] T003 [P] 建立 `.env.example` 和 `scripts/.env.docker` 中的 MCP 環境變數範本
- [x] T004 [P] 配置 linting 和格式化工具以支援新的 `src/youtube_search/mcp/` 模組

---

## 第 2 階段：基礎建設（所有故事的必要先決條件）

**目標**：核心基礎設施必須在任何用戶故事實現前完成

**⚠️ 關鍵**：在此階段完成前，不得開始用戶故事實現

- [x] T005 在 `src/youtube_search/config.py` 中新增 MCP 配置類，支援 MCP_SEARCH_TIMEOUT（預設 15 秒）和 MCP_SEARCH_RETRIES（預設 3 次）環境變數
- [x] T006 [P] 建立 `src/youtube_search/mcp/__init__.py` 的基本模組結構
- [x] T007 [P] 建立 `src/youtube_search/mcp/schemas.py` 作為 Pydantic 模型的基礎容器（留待各故事填充）
- [x] T008 [P] 建立 `src/youtube_search/mcp/tools/__init__.py` 工具模組基本結構
- [x] T009 建立 `src/youtube_search/mcp/router.py`，為 FastAPI 路由掛載預留空間
- [x] T010 在 `tests/` 目錄下建立 `unit/` 和 `integration/` 的 MCP 測試檔案骨架

**檢查點**：基礎設施就位 - 用戶故事實現現可並行開始

---

## 第 3 階段：用戶故事 1 - MCP 伺服器基礎功能（優先級：P1）🎯 MVP 核心

**目標**：建立符合 MCP 協定標準的伺服器，支持客戶端連接、工具列表查詢和連接生命週期管理。

**獨立測試**：可透過標準 MCP 客戶端（如 Claude Desktop）連接到伺服器，執行協定握手，查詢工具列表，驗證無故障的連接中斷。

### 用戶故事 1 測試（煙測試）

- [x] T011 [P] [US1] 在 `tests/integration/test_mcp_server_connection.py` 中建立 MCP 連接測試
- [x] T012 [P] [US1] 在 `tests/integration/test_mcp_server_tools.py` 中建立工具列表查詢測試

### 用戶故事 1 實現

- [x] T013 [US1] 在 `src/youtube_search/mcp/server.py` 中實現 MCP 伺服器實例初始化和 StreamableHTTPSessionManager 配置（滿足 FR-001）
- [x] T014 [US1] 在 `src/youtube_search/mcp/server.py` 中實現連接生命週期管理（握手、協定協商、優雅關閉）（滿足 US1 接受情景 1 和 4）
- [x] T015 [US1] 在 `src/youtube_search/mcp/server.py` 中實現工具註冊機制和工具列表查詢端點（滿足 FR-002 和 US1 接受情景 2）
- [x] T016 [US1] 在 `src/youtube_search/mcp/server.py` 中新增日誌記錄連接和列表工具的事件
- [x] T017 [US1] 在 `src/youtube_search/mcp/router.py` 中建立 FastAPI 路由掛載基礎（預留工具調用端點）

**檢查點**：用戶故事 1 應該完全功能正常且可獨立測試 - MCP 伺服器基礎就位

---

## 第 4 階段：用戶故事 2 - YouTube 搜尋工具整合（優先級：P1）🎯 MVP 核心

**目標**：將現有 YouTube 搜尋 API 功能封裝為 MCP 工具，AI 助手可透過 MCP 協定調用並獲取影片搜尋結果及完整 metadata。

**獨立測試**：可透過 MCP 客戶端直接調用 youtube_search 工具，傳入關鍵字和參數，驗證返回的影片資訊格式正確、包含必要 metadata、結果數量符合限制。無需依賴其他 MCP 功能即可完整測試此工具。

### 用戶故事 2 測試（煙測試 + 主要功能）

- [x] T018 [P] [US2] 在 `tests/unit/test_youtube_search_tool_basic.py` 中建立基本工具調用測試（關鍵字搜尋、結果排序）
- [x] T019 [P] [US2] 在 `tests/unit/test_youtube_search_tool_basic.py` 中建立 limit 參數測試和無結果情況測試

### 用戶故事 2 實現

- [x] T020 [P] [US2] 在 `src/youtube_search/mcp/schemas.py` 中定義 `YouTubeSearchInput` 和 `YouTubeSearchOutput` Pydantic 模型，支援關鍵字、limit（預設 1）、sort_by（預設 relevance）參數（滿足 FR-003 和 FR-005）
- [x] T021 [US2] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現 YouTube 搜尋 MCP 工具類，定義工具名稱、描述、完整參數定義（滿足 FR-003 和 FR-011）
- [x] T022 [US2] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現工具執行邏輯，呼叫現有 `SearchService` 並將 `Video` 模型映射到 MCP 回應格式（滿足 FR-004、FR-005 和 US2 接受情景 1-3）
- [x] T023 [US2] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現無結果時返回空清單的邏輯和結果超過 100 條時的截斷邏輯（滿足 US2 接受情景 4 和 6）
- [x] T024 [US2] 在 `src/youtube_search/mcp/server.py` 中註冊 youtube_search 工具到 MCP 伺服器（滿足 FR-002）
- [x] T025 [US2] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中新增日誌記錄工具調用和搜尋結果的事件（滿足 FR-009）

**檢查點**：用戶故事 1 和 2 都應該獨立功能正常 - MCP 搜尋工具已可使用

---

## 第 5 階段：用戶故事 3 - 工具參數驗證與錯誤處理（優先級：P2）🎯 MVP 品質

**目標**：實現完整的參數驗證機制和描述性錯誤回應，確保 AI 助手能理解問題並自我修正，系統在搜尋服務故障時優雅降級。

**獨立測試**：可獨立測試各種無效參數組合（空關鍵字、超出範圍的 limit、無效的 sort_by）以及服務故障情況（YouTube 不可用、Redis 快取故障），驗證每種情況都返回適當且清晰的錯誤訊息。

### 用戶故事 3 測試（參數驗證 + 錯誤處理）

- [x] T026 [P] [US3] 在 `tests/unit/test_youtube_search_tool_validation.py` 中建立空關鍵字、limit 超出範圍、sort_by 無效值的驗證測試（滿足 US3 接受情景 1-3）
- [x] T027 [P] [US3] 在 `tests/unit/test_youtube_search_tool_errors.py` 中建立 YouTube 服務不可用的錯誤處理測試（滿足 US3 接受情景 4）
- [x] T028 [P] [US3] 在 `tests/unit/test_youtube_search_tool_errors.py` 中建立 Redis 快取故障降級測試和畸形 JSON 請求測試（滿足 US3 接受情景 5-6）

### 用戶故事 3 實現

- [x] T029 [P] [US3] 在 `src/youtube_search/mcp/schemas.py` 中實現 `YouTubeSearchInput` 的參數驗證邏輯（關鍵字非空且 1-200 字符、limit 1-100、sort_by 只能是 'relevance' 或 'date'）（滿足 FR-006）
- [x] T030 [US3] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現詳細的驗證錯誤訊息，返回 `INVALID_KEYWORD`、`INVALID_LIMIT`、`INVALID_SORT` 等特定錯誤代碼（滿足 FR-007 和 US3 接受情景 1-3）
- [x] T031 [US3] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現 YouTube 服務不可用的錯誤捕捉和回應 `SERVICE_UNAVAILABLE` 錯誤訊息，建議稍後重試（滿足 FR-008 和 US3 接受情景 4）
- [x] T032 [US3] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中實現 Redis 快取故障的自動降級邏輯（無法連接快取時使用直接搜尋，記錄 WARN 級別日誌）（滿足 US3 接受情景 5）
- [x] T033 [US3] 在 `src/youtube_search/mcp/server.py` 中實現畸形 JSON 請求的捕捉和返回有效的 MCP 錯誤回應 `INVALID_REQUEST`（滿足 FR-014 和 US3 接受情景 6）
- [x] T034 [US3] 在 `src/youtube_search/mcp/tools/youtube_search.py` 中新增所有驗證和錯誤事件的日誌記錄（滿足 FR-009）
- [x] T035 [US3] 在 `src/youtube_search/mcp/server.py` 中實現連接中斷偵測和 1 秒內的資源釋放機制，防止孤立連接（滿足 FR-015）

**檢查點**：所有用戶故事 1、2、3 應該都是獨立且完全功能正常的 - MVP 核心完成

---

## 第 6 階段：整合與測試（第 3 階段）

**目標**：整合所有組件到主應用，進行端到端測試和部署驗證。

### 6.1 FastAPI 應用整合

- [x] T036 [US1] 在 `main.py` 中掛載 MCP 路由，設定應用生命週期以初始化 MCP 伺服器（滿足 FR-001、FR-013）
- [x] T037 [US1] 驗證 FastAPI 和 MCP 伺服器共存無衝突，既有 REST API 不受影響

### 6.2 系統整合測試

- [x] T038 [US1] 在 `tests/integration/test_mcp_end_to_end.py` 中建立完整流程測試：連接 → 列表工具 → 調用工具 → 斷開連接
- [x] T039 [P] [US2] 在 `tests/integration/test_mcp_end_to_end.py` 中建立多客戶端併發測試（至少 3 個並發客戶端）（滿足 SC-004）
- [x] T040 [P] [US3] 在 `tests/integration/test_mcp_end_to_end.py` 中建立參數驗證 + 錯誤恢復的整合測試
- [x] T041 [US1] 在 `tests/integration/test_mcp_end_to_end.py` 中建立超時和重試機制的整合測試（滿足 FR-010）
- [x] T042 [US1] 在 `tests/integration/test_mcp_end_to_end.py` 中驗證既有 REST API 與 MCP 功能無相互干擾

### 6.3 Docker 部署驗證

- [x] T043 驗證 `Dockerfile` 包含所有 MCP 層依賴，使用 `./scripts/build_docker.sh --platform arm64 --action build` 成功構建
- [x] T044 使用 `./scripts/run_docker.sh up` 啟動容器，驗證 MCP 伺服器正常執行
- [x] T045 使用 `./scripts/run_docker.sh logs` 查看日誌，確認 MCP 伺服器啟動訊息
- [x] T046 [P] 驗證從主機連接到容器中的 MCP 伺服器（預設埠 8441），執行基本工具調用
- [x] T047 [P] 驗證環境變數配置正確加載（MCP_SEARCH_TIMEOUT、MCP_SEARCH_RETRIES）
- [x] T048 使用 `./scripts/run_docker.sh down` 正確清理容器

### 6.4 文件和發布準備

- [x] T049 [P] 在 `README.md` 中新增 MCP 功能說明和快速開始指南（參考 `quickstart.md` 內容）
- [x] T050 [P] 在 `README.md` 中新增 MCP 環境變數配置說明（MCP_SEARCH_TIMEOUT、MCP_SEARCH_RETRIES）
- [x] T051 [P] 在 `README.md` 中新增 Docker 使用指南（參考 `scripts/build_docker.sh` 和 `scripts/run_docker.sh` 用法）
- [x] T052 更新 `scripts/.env.docker` 新增 MCP 環境變數範本
- [x] T053 更新 `.env.example` 新增 MCP 環境變數（主應用用）
- [x] T054 確保 `quickstart.md` 包含完整的開發環境設置和 Docker 部署說明
- [x] T055 [P] 最終程式碼審查和清理（確認所有新代碼符合現有代碼風格和 coding guidelines）

**檢查點**：MVP 完成 - MCP 支援功能已整合、測試、記錄

---

## 第 7 階段：波蘭與跨切關注（後續優化）

**目標**：改善多個用戶故事涉及的項目。

- [x] T056 [P] 附加單元測試（如果請求）在 `tests/unit/` 中涵蓋邊界情況
- [x] T057 [P] 性能優化 - 評估和優化搜尋工具調用延遲（目標 90% < 3 秒，不含網路延遲）（滿足 SC-007）
- [x] T058 [P] 代碼清理和重構（移除臨時代碼、統一命名）
- [x] T059 安全加強 - 審查 MCP 工具參數處理，確保無注入漏洞
- [x] T060 驗證 `quickstart.md` 中的所有步驟

---

## 相依性與執行順序

### 階段相依性

- **第 1 階段（準備）**：無相依性 - 可立即開始
- **第 2 階段（基礎設施）**：依賴第 1 階段完成 - **阻止所有用戶故事**
- **第 3 階段（US1）**：依賴第 2 階段完成 - US1 無其他相依性
- **第 4 階段（US2）**：依賴第 2 階段完成 - 可與 US1 並行，但應在 US1 後整合
- **第 5 階段（US3）**：依賴第 2 階段完成 - 可與 US1/US2 並行，但在集成前建議 US1/US2 完成
- **第 6 階段（整合）**：依賴所有 US 完成
- **第 7 階段（波蘭）**：依賴第 6 階段完成

### 用戶故事相依性

- **US1（P1）**：可在基礎設施後開始 - 無其他故事相依
- **US2（P1）**：可在基礎設施後開始 - 應整合 US1 結果但獨立可測
- **US3（P2）**：可在基礎設施後開始 - 應增強 US1/US2 但獨立可測

### 並行機會

- 第 1 階段所有標記 [P] 的任務可並行執行
- 第 2 階段所有標記 [P] 的任務可並行執行（在第 1 階段完成後）
- 基礎設施完成後，US1、US2、US3 可由不同團隊成員並行工作
- 每個 US 內，所有標記 [P] 的任務可並行執行
- US 測試可與下一個 US 實現並行執行

### 並行範例：用戶故事 2

```bash
# 啟動 US2 的所有測試：
任務："在 tests/unit/test_youtube_search_tool_basic.py 中建立基本工具調用測試"
任務："在 tests/unit/test_youtube_search_tool_basic.py 中建立 limit 參數測試"

# 啟動 US2 的所有實現工作（在測試完成後）：
任務："定義 YouTubeSearchInput 和 YouTubeSearchOutput Pydantic 模型"
任務："實現 YouTube 搜尋 MCP 工具類"
```

---

## 實現策略

### MVP 首先（僅用戶故事 1 + 2）

1. 完成第 1 階段：準備
2. 完成第 2 階段：基礎設施（**關鍵** - 阻止所有故事）
3. 完成第 3 階段：用戶故事 1
4. 完成第 4 階段：用戶故事 2
5. 完成第 5 階段：用戶故事 3（第 2 個 P1 優先級故事，應與 MVP 一起）
6. **停止並驗證**：整合測試 US1、US2、US3 獨立工作
7. 完成第 6 階段：整合
8. **部署/演示 MVP**

### 漸進交付

1. 基礎設施 → 開始
2. 新增 US1 → 測試獨立 → 交付（MVP！）
3. 新增 US2 → 測試獨立 → 交付
4. 新增 US3 → 測試獨立 → 交付
5. 每個故事添加價值，無破壞先前故事

### 並行團隊策略

有多個開發者時：

1. 團隊一起完成準備 + 基礎設施
2. 基礎設施完成後：
   - 開發者 A：US1
   - 開發者 B：US2
   - 開發者 C：US3
3. 故事獨立完成和整合

---

## 注意事項

- [P] 任務 = 不同檔案，無相依性
- [Story] 標籤將任務映射到特定用戶故事以進行可追蹤性
- 每個用戶故事應可獨立完成和測試
- 在實現前驗證測試失敗
- 在每個任務或邏輯組後進行提交
- 在任何檢查點停止以驗證故事獨立工作
- 避免：模糊任務、相同檔案衝突、破壞獨立性的故事間相依

---

## 成功標準追蹤

| 標準 | 量化目標 | 驗證方式 | 相關任務 |
|------|---------|---------|---------|
| 功能完整性 | P1 + P2 全部實現 | 單元測試 + 整合測試通過 | T011-T035 |
| 測試覆蓋 | 煙測試 + 主要錯誤情況 | pytest 報告 | T011-T028 |
| 連接時間 | < 1 秒 | 手動計時或 benchmark | T011 |
| 工具調用成功率 | ≥ 95% | 整合測試結果 | T039 |
| 參數驗證 | 100% 無效參數返回有意義錯誤 | 參數驗證測試 | T026-T028 |
| 可用性 | 99.9%（服務故障時保持運行） | 集成測試 | T040-T041 |
| 錯誤訊息清晰度 | 4.5 分以上（5 分制） | 代碼審查 | T030-T033 |
| 文件完整性 | 文件存在且內容完整 | 檔案檢查 | T049-T054 |

---

## 時間表估計

| 階段 | 天數 | 說明 |
|------|------|------|
| 第 1 階段 | 0.5 天 | 準備和依賴配置 |
| 第 2 階段 | 1 天 | 基礎設施（關鍵路徑） |
| 第 3 階段（US1） | 1.5 天 | MCP 伺服器基礎 |
| 第 4 階段（US2） | 1.5 天 | YouTube 搜尋工具 |
| 第 5 階段（US3） | 1.5 天 | 參數驗證和錯誤處理 |
| 第 6 階段 | 1.5 天 | 整合、測試、部署驗證 |
| 第 7 階段 | 1 天 | 波蘭和優化（可選） |
| **總計** | **8.5 天** | MVP 完成（P1 + P2） |

**注意**：P3（配置管理）延後到後續迭代。
