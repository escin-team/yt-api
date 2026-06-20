# 實作計劃：YouTube 音檔下載 API

**分支**: `004-audio-download` | **日期**: 2025-12-09 | **規格**: [spec.md](./spec.md)
**輸入**: 功能規格來自 `/specs/004-audio-download/spec.md`

**語言**: 本文件與所有 `/speckit` 產出（plan/spec/tasks/checklist 等）必須使用正體中文撰寫

**備註**: 本模板由 `/speckit.plan` 命令填充。參閱 `.specify/templates/commands/plan.md` 瞭解執行流程。

## 摘要

本功能在現有 YouTube 搜尋 API 基礎上，新增使用 yt-dlp 下載 YouTube 影片並轉換為 128kbps MP3 音檔的能力。系統支援單一和批次下載，提供快取機制避免重複下載，並限制影片長度在 10 分鐘以內。音檔可透過公開連結（24小時有效）或直接串流方式提供，支援客戶端透過參數選擇返回格式。

## 技術上下文

**語言/版本**: Python 3.12+
**主要依賴**:

- FastAPI（現有，用於 API 端點）
- yt-dlp（新增，用於影片下載和音檔轉換）
- Redis（現有，用於快取管理）
- Pydantic（現有，用於數據驗證）
**儲存**:
- 檔案系統（音檔暫存和快取）
- Redis（快取索引和元數據）
**測試**: pytest（現有測試框架）
**目標平台**: Linux 伺服器（與現有 API 相同）
**專案類型**: 單一後端專案（擴展現有 FastAPI 應用）
**效能目標**:
- API 回應時間 < 2 秒（不含下載處理）
- 支援 10 個並發下載請求
- 快取命中回應 < 1 秒
**限制**:
- 僅支援 10 分鐘以內影片
- 固定 128kbps MP3 格式
- 音檔 24 小時後自動清理
- 單次批次下載上限 20 個影片
- 下載逾時 5 分鐘
**規模/範圍**:
- 新增 2-3 個 API 端點
- 新增 3-4 個服務層類別
- 新增 2-3 個模型類別
- 預計 ~500-800 行新代碼

## 憲法檢查

*關卡：必須在 Phase 0 研究前通過。Phase 1 設計後重新檢查。*

### ✅ I. POC 導向的最小測試

- 本功能為 POC，測試保持最小化
- 將編寫煙霧測試覆蓋核心下載流程
- 手動驗證必須確認主要流程（單一下載、快取、清理）
- 不使用 skip 標記隱藏已知問題

**評估**：✅ 通過 - 符合 POC 最小測試原則

### ✅ II. 清晰架構

- 下載服務將獨立於搜尋服務
- yt-dlp 集成將封裝在專用服務中
- 快取邏輯將使用依賴注入
- 業務邏輯與 API 層分離

**評估**：✅ 通過 - 遵循現有模塊化架構模式

### ✅ III. 顯式優於隱式

- 所有配置參數明確（音質、長度限制、逾時）
- format 參數由客戶端顯式指定
- 錯誤訊息具體說明失敗原因
- 檔案路徑和清理策略明確配置

**評估**：✅ 通過 - 所有決策明確且可配置

### ✅ IV. 簡單優先

- 使用現有 FastAPI 和 Redis 基礎設施
- 不引入新的消息隊列或複雜調度
- 直接使用 yt-dlp CLI 工具，無需自定義封裝
- 快取策略簡單：基於檔案存在和時間戳

**評估**：✅ 通過 - 解決方案保持簡單實用

### ✅ V. 可觀察性與安全性

- 所有下載請求將記錄日誌
- yt-dlp 錯誤將被捕獲並記錄
- 檔案路徑將使用安全編碼
- 無需額外敏感資訊（使用現有配置）
- 遵守 YouTube 服務條款限制

**評估**：✅ 通過 - 具備適當的日誌和安全措施

### ✅ VI. 正體中文文件

- 所有規格、計劃、任務使用正體中文
- 代碼註釋使用正體中文
- API 文檔使用正體中文

**評估**：✅ 通過 - 遵循正體中文要求

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

### 源代碼（倉庫根目錄）

```text
src/youtube_search/
├── api/
│   └── v1/
│       ├── download.py          # 新增：下載 API 端點
│       └── search.py             # 現有：搜尋 API
├── models/
│   ├── download.py               # 新增：下載請求/回應模型
│   ├── search.py                 # 現有：搜尋模型
│   └── video.py                  # 現有：影片模型
├── services/
│   ├── audio_downloader.py       # 新增：yt-dlp 集成服務
│   ├── cache_manager.py          # 新增：快取管理服務
│   ├── file_cleanup.py           # 新增：定期清理服務
│   └── search.py                 # 現有：搜尋服務
├── utils/
│   ├── validators.py             # 擴展：添加影片長度驗證
│   ├── errors.py                 # 擴展：添加下載相關錯誤
│   └── logger.py                 # 現有：日誌工具
└── config.py                     # 擴展：添加下載配置

tests/
├── unit/
│   ├── test_audio_downloader.py  # 新增：下載服務單元測試
│   ├── test_cache_manager.py     # 新增：快取管理測試
│   └── test_download_models.py   # 新增：模型驗證測試
└── integration/
    ├── test_download_api.py       # 新增：下載 API 集成測試
    └── test_download_workflow.py  # 新增：端到端下載流程測試
```

**結構決策**：擴展現有單一專案結構。新功能遵循現有的分層架構（models/services/api），與搜尋功能保持一致的組織方式。使用現有的 FastAPI 應用和 Redis 基礎設施。

## Complexity Tracking

**狀態**：無違規

本功能未引入任何違反憲法的複雜性：

- ✅ 無新增專案（擴展現有專案）
- ✅ 無複雜抽象層（使用直接服務調用）
- ✅ 無過度配置（使用現有配置系統）
- ✅ 測試保持最小（符合 POC 原則）

## Phase Breakdown

### Phase 0: 研究與發現 ✅ **完成**

**目標**：解決所有技術未知，確認設計決策

**產出**：

- ✅ `research.md` - 包含 8 個研究項目的完整技術研究
  - yt-dlp 集成策略
  - 音檔格式和轉換配置
  - 快取策略（Redis + 檔案系統）
  - 檔案儲存和清理機制
  - 錯誤處理和重試策略
  - 串流回應實作
  - 批次下載實作
  - 安全性考量

**時間估計**：已完成

---

### Phase 1: 設計與合約 ✅ **完成**

**前提條件**：Phase 0 完成

**目標**：定義數據模型、API 合約、開發指南

**產出**：

- ✅ `data-model.md` - 7 個核心實體定義
  - DownloadRequest（下載請求模型）
  - AudioFile（音檔模型）
  - DownloadLog（下載日誌模型）
  - DownloadAudioRequest（API 請求模型）
  - BatchDownloadRequest（批次請求模型）
  - DownloadAudioResponse（單一回應模型）
  - BatchDownloadResponse（批次回應模型）

- ✅ `contracts/openapi.yaml` - 完整 OpenAPI 3.1 規範
  - POST /api/v1/download/audio（單一下載）
  - POST /api/v1/download/batch（批次下載）
  - 所有請求/回應模式定義
  - 錯誤回應規範（400, 403, 404, 503, 507）

- ✅ `quickstart.md` - 開發者快速入門指南
  - 環境設定（FFmpeg, Redis）
  - API 使用範例（curl, Python）
  - 快取測試步驟
  - 錯誤處理測試
  - 故障排除指南

- ✅ Agent context 更新
  - GitHub Copilot instructions 已更新
  - 新增 yt-dlp 技術堆疊資訊

**時間估計**：已完成

---

### Phase 2: 實作計劃 ✅ **完成**

**前提條件**：Phase 1 完成

**目標**：生成可執行的工作任務列表

**產出**：

- ✅ `tasks.md` - 52 個詳細實作任務
  - 按使用者故事組織（US1-US4）
  - 7 個階段：設定、基礎設施、4 個使用者故事、優化
  - 明確的依賴關係和並行機會
  - MVP 範圍建議（T001-T021）
  - 時間估計：27-35 小時（單人）或 2-3 天（團隊）

**時間估計**：已完成

---

## 設計後憲法重新檢查

所有 Phase 1 產出（data-model.md, contracts/openapi.yaml, quickstart.md）已完成後重新評估憲法合規性：

### ✅ I. POC 導向的最小測試 - 重新確認

**設計審查**：

- 數據模型保持簡單，無過度抽象
- API 端點僅 2 個（單一下載、批次下載）
- 測試計劃僅涵蓋核心流程
- 無複雜的測試框架或 mock 層

**判定**：✅ 仍然通過 - 設計符合 POC 原則

### ✅ II. 清晰架構 - 重新確認

**設計審查**：

- 服務層清晰分離（audio_downloader, cache_manager, file_cleanup）
- 模型層獨立（download.py）
- API 層薄而直接（download.py）
- 依賴流：API → Services → Models

**判定**：✅ 仍然通過 - 架構清晰且模塊化

### ✅ III. 顯式優於隱式 - 重新確認

**設計審查**：

- OpenAPI 規範明確定義所有參數和回應
- 錯誤類型枚舉明確（DownloadErrorType）
- 快取行為明確記錄在回應中（cached 欄位）
- 所有配置參數在環境變數中明確定義

**判定**：✅ 仍然通過 - 所有行為明確可見

### ✅ IV. 簡單優先 - 重新確認

**設計審查**：

- 使用標準 HTTP POST 端點，無 WebSocket 或複雜協議
- Redis 快取使用簡單的鍵值對，無複雜查詢
- 檔案清理使用 cron + 簡單掃描，無複雜調度系統
- yt-dlp 直接使用命令行工具，無自定義封裝

**判定**：✅ 仍然通過 - 設計保持簡單實用

### ✅ V. 可觀察性與安全性 - 重新確認

**設計審查**：

- DownloadLog 模型捕獲所有下載活動
- 錯誤類型明確分類（video_not_found, duration_exceeded 等）
- 檔案路徑使用安全編碼（video_id 驗證）
- OpenAPI 規範包含完整錯誤文檔

**判定**：✅ 仍然通過 - 具備充分的可觀察性和安全措施

### ✅ VI. 正體中文文件 - 重新確認

**設計審查**：

- data-model.md 使用正體中文
- contracts/openapi.yaml 使用正體中文描述
- quickstart.md 使用正體中文
- 所有欄位說明和錯誤訊息使用正體中文

**判定**：✅ 仍然通過 - 完全符合正體中文要求

---

## 下一步

### 立即行動

**Phase 2** 已準備就緒。執行以下命令生成實作任務：

```bash
cd /Users/sacahan/Documents/workspace/YTSearch
/speckit.tasks
```

### 後續工作流程

1. ✅ Phase 0: 研究（已完成）
2. ✅ Phase 1: 設計（已完成）
3. ⏳ Phase 2: 任務生成（執行 `/speckit.tasks`）
4. 🔜 Phase 3: 實作（執行 `/speckit.implement`）
5. 🔜 Phase 4: 測試與驗證

### 驗證清單

在進入實作前，確認：

- [x] research.md 已完成所有技術決策
- [x] data-model.md 定義所有實體和關係
- [x] contracts/openapi.yaml 提供完整 API 規範
- [x] quickstart.md 提供開發者指南
- [x] 憲法檢查所有項目通過
- [x] Agent context 已更新
- [x] 執行 `/speckit.tasks` 生成任務列表

---

**計劃狀態**：✅ 所有計劃階段完成，準備開始實作
**最後更新**：2025-12-09
**分支**：004-audio-download
**下一個命令**：開始實作 Phase 1 設定任務（T001-T004）或使用 `/speckit.implement` 自動實作
