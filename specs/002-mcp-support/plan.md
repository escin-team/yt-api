# 實現計劃：MCP (Model Context Protocol) 支援

**分支**：`002-mcp-support` | **日期**：2025-12-07 | **規格**：[spec.md](spec.md)
**輸入**：功能規範來自 `/specs/002-mcp-support/spec.md`

**語言**：本文件與所有 `/speckit` 產出（plan/spec/tasks/checklist 等）必須使用正體中文撰寫

## 概述

將現有的 YouTube 搜尋 API 功能透過 MCP (Model Context Protocol) 協定暴露給 AI 助手（如 Claude Desktop）。整合使用官方 MCP Python SDK 的 StreamableHTTPSessionManager，透過 FastAPI 應用掛載 MCP 伺服器，複用現有的爬蟲架構和服務層。初期 MVP 包含 P1 + P2 功能：MCP 伺服器基礎 + YouTube 搜尋工具 + 完整的參數驗證與錯誤處理。

## 技術背景

**語言/版本**：Python 3.12+
**主要依賴**：FastAPI、MCP Python SDK (官方 /modelcontextprotocol/python-sdk)、Pydantic、requests、uvicorn
**存儲**：N/A（複用現有的 Redis 快取，可選）
**測試**：pytest + pytest-asyncio
**目標平台**：Docker 容器 on Ubuntu 主機
**專案類型**：單一 Python 後端應用（擴展現有 FastAPI 應用）
**效能目標**：
- 連接建立時間 < 1 秒
- 單次搜尋工具調用 < 15 秒（含重試）
- 並發客戶端支援 ≥ 10 個
- MCP 工具調用成功率 ≥ 95%

**約束**：
- POC 性質，最小化過度設計
- 基於現有架構擴展（不重構）
- 無需 YouTube Data API（成本控制）
- 使用環境變數進行超時配置

## 憲法檢查

**門檑評估**：✅ 通過

| 檢查項 | 評估 | 備註 |
|--------|------|------|
| POC 最小化測試 | ✅ 符合 | 寫煙測試即可，無需完整覆蓋 |
| 清潔架構 | ✅ 符合 | 複用現有服務層（SearchService、YouTubeScraper），新增工具層 |
| 顯式優於隱式 | ✅ 符合 | 環境變數明確配置超時，工具參數完全驗證 |
| 簡單優先 | ✅ 符合 | 直接整合官方 SDK，無自訂實現 |
| 可觀測與安全 | ✅ 符合 | 複用現有日誌系統，新增 MCP 層日誌 |
| 正體中文文件 | ✅ 符合 | 本計劃及所有輸出均使用正體中文 |

**通過**：此功能符合所有憲法原則，可進入 Phase 0。

## 專案結構

### 文檔（此功能）

```text
specs/002-mcp-support/
├── spec.md                    # 功能規範
├── plan.md                    # 本檔（實現計劃）
├── research.md                # Phase 0 輸出（研究產出）
├── data-model.md              # Phase 1 輸出（資料模型）
├── quickstart.md              # Phase 1 輸出（快速開始指南）
├── contracts/                 # Phase 1 輸出（API 契約）
│   └── mcp-tools.json         # MCP 工具定義
└── checklists/
    ├── requirements.md        # 需求檢查清單
    └── clarification-report.md# 澄清報告
```

### 原始碼（倉庫根目錄）

```text
src/youtube_search/
├── mcp/                       # ✨ 新增：MCP 層（此功能新增）
│   ├── __init__.py
│   ├── server.py              # MCP 伺服器實例和配置
│   ├── tools/                 # MCP 工具定義
│   │   ├── __init__.py
│   │   └── youtube_search.py  # YouTube 搜尋工具實現
│   ├── router.py              # FastAPI 路由掛載
│   └── schemas.py             # MCP 相關的 Pydantic 模型
├── models/                    # 既有：資料模型
├── services/                  # 既有：業務邏輯
├── api/                       # 既有：REST API
└── utils/                     # 既有：工具函數

tests/
├── unit/
│   ├── test_youtube_search_tool.py     # ✨ 新增：MCP 工具單元測試
│   └── ...（既有測試）
├── integration/
│   ├── test_mcp_server_integration.py  # ✨ 新增：MCP 伺服器整合測試
│   └── ...（既有測試）
└── ...（既有測試）

main.py                        # ✏️ 修改：整合 MCP 路由掛載
pyproject.toml                 # ✏️ 修改：新增 MCP SDK 依賴
Dockerfile                     # ✏️ 修改：確保 MCP 層包含
```

**結構決策**：採用選項 1（單一專案）延伸。MCP 層作為新的子模組 `src/youtube_search/mcp/`，整合到現有 FastAPI 應用中，複用現有的服務層和資料模型。

## 複雜性追蹤

| 設計決策 | 必要原因 | 為何簡單方案不足 |
|---------|---------|-----------------|
| MCP 工具層 | 封裝搜尋邏輯，提供 AI 友善的介面 | 直接暴露 REST API 無法讓 Claude Desktop 這樣的客戶端自動發現和調用工具 |
| StreamableHTTPSessionManager | FastAPI 整合的官方標準方式 | 自訂 HTTP 層實現會增加複雜性和維護負擔 |
| 環境變數超時配置 | 提供靈活性，無需重新編譯 | 硬編碼超時值無法適應不同的部署環境 |
| 參數驗證層（P2） | AI 助手需要清晰的錯誤回饋以自我修正 | 無驗證會導致 AI 助手陷入重試迴圈，浪費 token |

## 實現階段

### Phase 0：研究（1-2 天）

**目標**：建立完整的技術知識基礎，確保實現方向正確。

#### 0.1 MCP Python SDK 深度研習

- 研究官方 SDK 的 StreamableHTTPSessionManager 用法
- 學習工具定義語法和參數驗證機制
- 研究錯誤回應格式和最佳實踐
- 查找官方示例代碼

**產出**：`research.md` 中的 MCP SDK 部分

#### 0.2 FastAPI 整合模式研究

- 研究如何將 Starlette 應用掛載到 FastAPI 中
- 學習 StreamableHTTP 傳輸層的工作原理
- 研究如何在 FastAPI 生命週期中管理 MCP 連接

**產出**：`research.md` 中的 FastAPI 整合部分

#### 0.3 現有架構適配研究

- 分析現有 `SearchService` 和 `YouTubeScraper` 的介面
- 研究如何將它們的回傳值映射到 MCP 工具格式
- 識別可能的集成點和相依性

**產出**：`research.md` 中的架構適配部分

**交付物**：
- `research.md` - 完整的研究報告（包含代碼示例）

---

### Phase 1：設計與契約（2-3 天）

**目標**：定義 MCP 層的完整設計、資料模型和 API 契約。

#### 1.1 MCP 工具設計

**工作項**：定義 youtube_search 工具的完整規格

**交付物**：
- 工具名稱、描述、參數定義
- 參數驗證規則
- 回應格式定義
- 錯誤情況和錯誤訊息

**接受標準**：
- 工具定義包含所有 P2 驗證規則
- 支援所有接受情景（故事 1-3）
- 錯誤訊息清晰且可被 AI 理解

**範例**：
```json
{
  "name": "youtube_search",
  "description": "搜尋 YouTube 影片",
  "inputSchema": {
    "type": "object",
    "properties": {
      "keyword": {
        "type": "string",
        "description": "搜尋關鍵字（必填，1-200 字符）"
      },
      "limit": {
        "type": "integer",
        "description": "結果數量限制（選填，1-100，預設 1）"
      },
      "sort_by": {
        "type": "string",
        "enum": ["relevance", "date"],
        "description": "排序方式（選填，預設 relevance）"
      }
    },
    "required": ["keyword"]
  }
}
```

#### 1.2 資料模型設計

**工作項**：定義 MCP 層的 Pydantic 模型

**交付物**：`data-model.md` 包含：
- `MCPTool` - MCP 工具基類
- `YouTubeSearchTool` - YouTube 搜尋工具實例
- `ToolInput` - 工具輸入驗證模型
- `ToolOutput` - 工具輸出格式模型
- `ToolError` - 錯誤回應模型

**接受標準**：
- 所有模型使用 Pydantic v2
- 包含完整的驗證邏輯和錯誤訊息

#### 1.3 API 契約定義

**工作項**：定義 MCP 伺服器的 HTTP 端點契約

**交付物**：`contracts/mcp-tools.json` - OpenAPI 風格的工具定義

**端點**：
- `GET /mcp/tools` - 列出可用工具
- `POST /mcp/tools/call` - 調用工具

#### 1.4 快速開始指南

**工作項**：編寫開發者快速開始文檔

**交付物**：`quickstart.md` 包含：
- 環境設置步驟
- MCP 伺服器啟動方式
- 本地測試步驟
- Claude Desktop 配置示例

**交付物總結**：
- `data-model.md` - 完整的資料模型設計
- `quickstart.md` - 開發者快速開始指南
- `contracts/mcp-tools.json` - 工具 API 契約

---

### Phase 2：實現（4-5 天）

**目標**：實現 MCP 層的核心功能（P1 + P2）。

#### 2.1 MCP 伺服器基礎設施（P1）

**工作項**：建立 MCP 伺服器實例和 FastAPI 整合

**檔案**：
- `src/youtube_search/mcp/__init__.py`
- `src/youtube_search/mcp/server.py`
- `src/youtube_search/mcp/router.py`

**實現內容**：
1. 建立 MCP Server 實例
2. 配置 StreamableHTTPSessionManager
3. 實現 FastAPI 掛載邏輯
4. 管理連接生命週期

**接受標準**：
- MCP 客戶端能成功連接（SC-001）
- 列出工具端點工作正常
- 連接優雅關閉

**測試**：
```bash
# 煙測試：連接和列出工具
pytest tests/integration/test_mcp_server_integration.py::test_mcp_server_connection
pytest tests/integration/test_mcp_server_integration.py::test_list_tools
```

**估時**：1 天

#### 2.2 YouTube 搜尋工具實現（P1）

**工作項**：實現 youtube_search MCP 工具

**檔案**：
- `src/youtube_search/mcp/tools/__init__.py`
- `src/youtube_search/mcp/tools/youtube_search.py`
- `src/youtube_search/mcp/schemas.py`

**實現內容**：
1. 定義工具類，包含名稱、描述、參數定義
2. 實現工具執行邏輯，呼叫 SearchService
3. 將 SearchService 回傳的 Video 模型映射到 MCP 回應格式
4. 實現基本的錯誤處理

**接受標準**：
- 工具調用返回正確的結果（故事 2 的接受情景 1-2）
- 結果格式符合 MCP 標準（SC-003）
- 搜尋無結果時返回空清單

**測試**：
```bash
pytest tests/unit/test_youtube_search_tool.py::test_tool_call_with_keyword
pytest tests/unit/test_youtube_search_tool.py::test_tool_call_with_limit
pytest tests/unit/test_youtube_search_tool.py::test_tool_call_no_results
```

**估時**：1.5 天

#### 2.3 參數驗證與錯誤處理（P2）

**工作項**：實現完整的參數驗證和錯誤回應

**檔案**：
- `src/youtube_search/mcp/tools/youtube_search.py` - 增強
- `src/youtube_search/mcp/schemas.py` - 增強

**實現內容**：
1. 實現關鍵字驗證（非空、長度限制）
2. 實現 limit 參數驗證（範圍 1-100）
3. 實現 sort_by 參數驗證（只允許 relevance/date）
4. 實現 YouTube 服務錯誤的優雅降級
5. 實現 Redis 快取故障的降級
6. 實現清晰的錯誤訊息格式

**接受標準**：
- 所有無效參數組合返回適當錯誤訊息（故事 3）
- 參數驗證捕捉 100% 的無效情況（SC-005）
- 錯誤訊息清晰可理解（SC-008）
- 服務故障時優雅降級（SC-006）

**測試**：
```bash
pytest tests/unit/test_youtube_search_tool.py::test_validation_empty_keyword
pytest tests/unit/test_youtube_search_tool.py::test_validation_invalid_limit
pytest tests/unit/test_youtube_search_tool.py::test_validation_invalid_sort_by
pytest tests/unit/test_youtube_search_tool.py::test_youtube_service_error_handling
pytest tests/unit/test_youtube_search_tool.py::test_cache_service_degradation
```

**估時**：1.5 天

#### 2.4 日誌與監控集成（P2）

**工作項**：整合日誌系統記錄 MCP 工具調用

**檔案**：
- `src/youtube_search/mcp/server.py` - 增強
- `src/youtube_search/mcp/tools/youtube_search.py` - 增強

**實現內容**：
1. 在 MCP 伺服器層記錄連接事件
2. 在工具層記錄所有調用和參數
3. 記錄錯誤和降級事件
4. 複用現有的日誌系統

**接受標準**：
- 所有 MCP 事件都被記錄（FR-009）
- 日誌訊息清晰且有用於故障排除

**估時**：0.5 天

#### 2.5 環境變數配置（P2）

**工作項**：實現超時和重試配置

**檔案**：
- `src/youtube_search/config.py` - 增強
- `src/youtube_search/mcp/server.py` - 增強

**實現內容**：
1. 添加 MCP_SEARCH_TIMEOUT（預設 15 秒）
2. 添加 MCP_SEARCH_RETRIES（預設 3 次）
3. 在 SearchService 中實現重試邏輯
4. 在工具層應用超時

**接受標準**：
- 環境變數正確讀取和應用
- 超時和重試在工具調用中生效

**估時**：0.5 天

**Phase 2 交付物**：
- `src/youtube_search/mcp/` - 完整的 MCP 層實現
- `tests/unit/test_youtube_search_tool.py` - 工具單元測試
- `tests/integration/test_mcp_server_integration.py` - 伺服器整合測試
- `.env.example` 更新 - 新增 MCP 環境變數示例

---

### Phase 3：整合與測試（2-3 天）

**目標**：整合所有組件，進行系統測試和部署準備。

#### 3.1 FastAPI 應用整合

**工作項**：將 MCP 路由整合到主 FastAPI 應用

**檔案**：
- `main.py` - 修改

**實現內容**：
1. 在 main.py 中掛載 MCP 路由
2. 配置應用生命週期以管理 MCP 連接
3. 確保 MCP 層在應用啟動時初始化

**接受標準**：
- 應用啟動時 MCP 伺服器正確初始化
- FastAPI 和 MCP 共存無衝突

**估時**：0.5 天

#### 3.2 系統整合測試

**工作項**：端到端整合測試

**測試場景**：
1. 完整流程：連接 → 列表工具 → 調用工具 → 斷開連接
2. 多客戶端併發（至少 3 個客戶端）
3. 參數驗證 + 錯誤恢復
4. 超時和重試機制
5. 與現有 REST API 的互不干擾

**測試代碼位置**：
- `tests/integration/test_mcp_end_to_end.py`

**接受標準**：
- 所有成功標準通過（SC-001 ~ SC-008）
- 無回歸：既有 API 功能不受影響

**估時**：1 天

#### 3.3 Docker 部署驗證

**工作項**：驗證 Docker 容器中的 MCP 功能（遵循 `scripts/build_docker.sh` 和 `scripts/run_docker.sh`）

**檔案**：
- `Dockerfile` - 驗證並確保 MCP 層依賴包含
- `scripts/build_docker.sh` - 多平台構建腳本（arm64/amd64）
- `scripts/run_docker.sh` - 容器運行和管理腳本
- `scripts/.env.docker` - Docker 環境配置

**驗證內容**：
1. 使用 `./scripts/build_docker.sh --platform arm64 --action build` 構建映像（包含 MCP 層）
2. 使用 `./scripts/run_docker.sh up` 啟動容器
3. 使用 `./scripts/run_docker.sh logs` 查看日誌驗證 MCP 伺服器正常運行
4. 使用 `./scripts/run_docker.sh shell` 進入容器進行手動驗證
5. 測試外部 MCP 客戶端連接到容器中的 MCP 伺服器
6. 使用 `./scripts/run_docker.sh down` 正確清理容器

**接受標準**：
- ✅ Docker 映像構建成功（支援多平台 arm64/amd64）
- ✅ 容器正常啟動，MCP 伺服器在日誌中顯示啟動訊息
- ✅ 可從主機連接到容器中的 MCP 伺服器（預設埠位：8441）
- ✅ 容器生命周期管理正常（啟動、停止、重啟、日誌查看）
- ✅ 環境變數配置正確加載（MCP_SEARCH_TIMEOUT、MCP_SEARCH_RETRIES）

**注意**：參考現行最佳實踐
- `build_docker.sh`：支援互動式選擇平台（arm64/amd64/all）和操作（build/push/build-push）
- `run_docker.sh`：提供完整的容器生命周期管理（up/down/restart/pull/logs/shell/clean）
- Docker 網路：自動建立並使用 `sacahan-network`
- 日誌目錄：掛載 `scripts/logs/` 以供外部查看應用日誌

**估時**：0.5 天

#### 3.4 文件和發布準備

**工作項**：完成文件、更新依賴、準備發布

**檔案**：
- `pyproject.toml` - 新增 mcp 依賴
- `README.md` - 新增 MCP 功能部分和 Docker 使用指南
- `scripts/.env.docker` - Docker 環境配置模板
- `.env.example` - 新增 MCP 配置（主應用用）
- `Dockerfile` - 如需調整以支援 MCP 層

**內容**：
1. 在 pyproject.toml 中新增 `mcp>=1.0.0` 及相關依賴
2. 更新 README.md：
   - 說明 MCP 功能特性
   - MCP 伺服器配置和環境變數（MCP_SEARCH_TIMEOUT、MCP_SEARCH_RETRIES）
   - Docker 使用指南（參考 `scripts/build_docker.sh` 和 `scripts/run_docker.sh` 用法）
   - 快速開始：`./scripts/build_docker.sh --platform arm64 --action build` → `./scripts/run_docker.sh up`
3. 在 `scripts/.env.docker` 中新增 MCP 環境變數範例
4. 在 `.env.example` 中新增 MCP 環境變數（主應用用）
5. 確保 `quickstart.md` 包含 Docker 部署說明

**估時**：0.5 天

**Phase 3 交付物**：
- 完整的整合系統（MCP + 既有 API）
- `tests/integration/test_mcp_end_to_end.py` - 系統整合測試
- 驗證的 Docker 配置（Dockerfile + build_docker.sh + run_docker.sh）
- 完整的文件（README、.env.example、quickstart.md）
- `pyproject.toml` 包含新依賴和版本資訊

---

## 工作項摘要

| 工作項 | 優先級 | 估時 | 相依性 | 狀態 |
|--------|--------|------|--------|------|
| Phase 0.1：MCP SDK 研究 | P0 | 0.5 天 | 無 | 待開始 |
| Phase 0.2：FastAPI 整合研究 | P0 | 0.5 天 | 無 | 待開始 |
| Phase 0.3：架構適配研究 | P0 | 0.5 天 | 無 | 待開始 |
| Phase 1.1：工具設計 | P1 | 0.5 天 | Phase 0 完成 | 待開始 |
| Phase 1.2：資料模型設計 | P1 | 0.5 天 | Phase 0 完成 | 待開始 |
| Phase 1.3：API 契約定義 | P1 | 0.5 天 | Phase 1.1 完成 | 待開始 |
| Phase 1.4：快速開始指南 | P1 | 0.5 天 | Phase 1.1-1.3 完成 | 待開始 |
| Phase 2.1：MCP 伺服器基礎 | P1 | 1 天 | Phase 1 完成 | 待開始 |
| Phase 2.2：YouTube 工具實現 | P1 | 1.5 天 | Phase 2.1 完成 | 待開始 |
| Phase 2.3：參數驗證與錯誤處理 | P2 | 1.5 天 | Phase 2.2 完成 | 待開始 |
| Phase 2.4：日誌集成 | P2 | 0.5 天 | Phase 2.1 完成 | 待開始 |
| Phase 2.5：環境變數配置 | P2 | 0.5 天 | Phase 2.1 完成 | 待開始 |
| Phase 3.1：FastAPI 整合 | P1 | 0.5 天 | Phase 2 完成 | 待開始 |
| Phase 3.2：系統整合測試 | P1 | 1 天 | Phase 3.1 完成 | 待開始 |
| Phase 3.3：Docker 驗證 | P1 | 0.5 天 | Phase 3.1 完成 | 待開始 |
| Phase 3.4：文件和發布 | P1 | 0.5 天 | Phase 3 完成 | 待開始 |
| **總計** | - | **10 天** | - | - |

## 時間表

```
週 1：
├─ Day 1-2：Phase 0（研究）- 1.5 天
├─ Day 2-3：Phase 1（設計）- 2 天
└─ Day 4-6：Phase 2（實現）- 3 天

週 2：
├─ Day 7-8：Phase 2 繼續（實現）- 1.5 天
└─ Day 8-10：Phase 3（整合測試）- 2.5 天

里程碑：
✓ Day 1.5：研究完成，可進入設計
✓ Day 3.5：設計完成，可進入實現
✓ Day 6：P1 功能基本完成
✓ Day 7.5：P2 功能完成
✓ Day 10：MVP 完成，可部署
```

## 成功標準

| 標準 | 量化目標 | 驗證方式 |
|------|---------|---------|
| 功能完整性 | P1 + P2 全部實現 | 單元測試 + 整合測試通過 |
| 測試覆蓋 | ≥ 煙測試（快樂路徑 + 主要錯誤情況） | pytest 報告 |
| 連接時間 | < 1 秒 | 手動計時或 benchmark 測試 |
| 工具調用 | 成功率 ≥ 95% | 整合測試結果 |
| 錯誤處理 | 100% 無效參數返回有意義錯誤 | 參數驗證測試 |
| 可靠性 | 連續運行 100 次調用無崩潰 | 壓力測試 |
| 文件完整性 | data-model.md + quickstart.md + contracts | 檔案存在且內容完整 |

## 資源

### 團隊
- 開發者 1 人（全職）
- 建議時間分配：
  - 研究 + 設計：20%
  - 實現：60%
  - 測試 + 整合：20%

### 工具
- Python 3.12+
- uv（依賴管理）
- pytest（測試）
- Docker（部署）
- Claude Desktop 或其他 MCP 客戶端（測試）

### 外部資源
- MCP Python SDK 官方文件
- FastAPI 官方文件
- 現有專案代碼（SearchService、YouTubeScraper）

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解策略 |
|------|--------|------|---------|
| MCP SDK API 變更 | 低 | 中 | 使用官方穩定版本，定期檢查更新 |
| FastAPI 與 MCP 整合複雜性 | 低 | 中 | 官方 SDK 提供完整支援，有範例代碼 |
| 爬蟲性能導致超時 | 中 | 中 | 環境變數可配置超時，實現重試機制 |
| YouTube 結構變更 | 中 | 低 | 複用現有爬蟲（已驗證可用），監控變化 |
| 測試不充分 | 低 | 低 | 基於 POC 最小測試原則，手動驗證核心流程 |

## 後續迭代（P3）

P3 功能（MCP 伺服器配置管理）延後到後續迭代：
- 配置檔案支援（.env、YAML）
- 連接埠配置
- 日誌級別動態調整
- 工具註冊的插件機制
- 監控和指標收集

## 附錄：關鍵決策

### 為什麼選擇 StreamableHTTPSessionManager？

StreamableHTTPSessionManager 是官方 MCP Python SDK 提供的標準方式，用於將 MCP 伺服器整合到 FastAPI 應用。相比自訂實現，它：
- ✅ 官方支援，有完整文件
- ✅ 與 Starlette 無縫整合
- ✅ 處理複雜的 HTTP 流管理
- ✅ 生產級別的穩定性

### 為什麼在 MVP 中包含 P2？

參數驗證和錯誤處理（P2）在 MVP 中實現的原因：
- ✅ 無這些功能，AI 助手會陷入重試迴圈
- ✅ 錯誤訊息對 AI 自我修正至關重要
- ✅ 增加開發時間不多（1.5 天）
- ✅ 大幅提升用戶體驗

### 為什麼不使用 YouTube Data API？

維持爬蟲方式的原因：
- ✅ 零成本（Data API 有配額限制和費用）
- ✅ 現有實現已驗證可用
- ✅ 符合專案的成本控制目標
- ⚠️ 風險：YouTube 結構變更。緩解：監控並快速適應


## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
