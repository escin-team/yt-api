# 實現計劃：YouTube 搜尋 API

**分支**：`001-youtube-search-api` | **日期**：2025-12-07 | **規範**：`spec.md`
**輸入**：功能規範來自 `/specs/001-youtube-search-api/spec.md`

**語言**：本文件與所有 `/speckit` 產出（plan/spec/tasks/checklist 等）必須使用正體中文撰寫

**注記**：此文件由 `/speckit.plan` 命令填寫。詳見 `.specify/templates/commands/plan.md` 執行工作流。

## 摘要

透過爬蟲 YouTube 搜尋結果頁面（而非官方 API）實現成本最優化的影片搜尋 API。系統接受關鍵字輸入，提取 ytInitialData JSON 結構中的影片 metadata（video_id、title、channel 等），以 RESTful 格式返回，並使用 Redis 快取 1 小時優化重複查詢。POC 階段優先功能可用性，支援預設 1 筆或自訂 1-100 筆結果限制。

## 技術背景

**語言/版本**：Python 3.12+（PEP 8/20/257 遵循）
**主要依賴**：FastAPI、Pydantic、requests、redis、pytest（可選）
**儲存**：Redis（快取層）；無永久資料庫（POC 階段）
**測試**：pytest（可選，POC 階段僅煙霧測試）
**目標平台**：Linux/macOS 伺服器（REST API 服務）
**專案類型**：web（FastAPI 後端）
**效能目標**：單筆搜尋 3 秒內返回（含網路延遲）

**約束**：

- 無官方 YouTube API 配額
- 遵守 YouTube ToS（不下載/儲存媒體內容）
- POC 階段無併發優化（非大規模部署）
- 爬蟲依賴 YouTube 頁面結構穩定性（變化風險）

**擴展性**：

- P1 核心功能：基本搜尋 + metadata 提取
- P2 擴展功能：排序/過濾/分頁（後續迭代）

## 憲章檢查

*門禁：Phase 0 前必須通過。Phase 1 後重新檢查。*

### 原則遵循評估

| 原則 | 狀態 | 決策/證據 |
|------|------|----------|
| **I. POC 最小化測試** | ✅ Pass | 規範明確標記 POC 階段，測試可選；POC 驗證成功確認可行性 |
| **II. 清潔架構** | ✅ Pass | 計劃包含分層架構：爬蟲層、提取層、API 層、快取層（獨立可測） |
| **III. 明確勝過隱含** | ✅ Pass | 規範明確定義所有參數、錯誤處理、metadata 策略、Redis 配置 |
| **IV. 簡潔優先** | ✅ Pass | 使用現成工具（requests、re、json），不自建複雜爬蟲框架 |
| **V. 程式碼即配置** | ✅ Pass | Redis 連線參數完全由環境變數控制（REDIS_HOST 等），可無碼配置 |
| **VI. 正體中文文件** | ✅ Pass | 規範與計劃均採正體中文撰寫（NON-NEGOTIABLE） |

### 結論

✅ **通過**：所有 6 項原則符合，可進入 Phase 0

## 專案結構

### 文件（此功能）

```text
specs/001-youtube-search-api/
├── plan.md              # 此檔案（/speckit.plan 命令輸出）
├── research.md          # Phase 0 輸出（本命令生成）
├── data-model.md        # Phase 1 輸出（本命令生成）
├── quickstart.md        # Phase 1 輸出（本命令生成）
├── contracts/           # Phase 1 輸出（本命令生成）
│   └── openapi.yaml
├── spec.md              # 功能規範（已存在）
└── checklists/
    └── requirements.md
```

### 原始碼（倉庫根目錄）

```text
src/
├── __init__.py
├── models/                  # Pydantic 數據模型
│   ├── __init__.py
│   ├── video.py             # Video 實體
│   └── search.py            # SearchResult 實體
├── services/                # 業務邏輯層
│   ├── __init__.py
│   ├── scraper.py           # YouTube 爬蟲邏輯
│   ├── cache.py             # Redis 快取管理
│   └── search.py            # 搜尋協調服務
├── api/                     # API 端點層
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── search.py        # GET /api/v1/search 端點
├── utils/                   # 工具函式庫
│   ├── __init__.py
│   ├── validators.py        # 輸入驗證
│   ├── errors.py            # 自訂例外
│   └── logger.py            # 結構化日誌
└── config.py                # 環境配置

tests/
├── unit/                    # 單元測試
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_services.py
├── integration/             # 整合測試（可選）
│   └── test_api.py
└── conftest.py

main.py                       # FastAPI 應用入口
pyproject.toml               # 專案配置 + 套件管理（uv）
Dockerfile                   # （選擇性部署）
.env.example                 # 環境變數範本
```

**結構決策**：簡化為 `src/` 直接模組結構（無冗余嵌套）。按層次分割（models → services → api）以保持清潔架構，模組可透過 `from src.models import Video` 直接匯入。

## Phase 0：輪廓與研究

### 研究清單

根據規範和澄清會話，以下主題已明確或需進一步研究：

| # | 主題 | 狀態 | 說明 |
|----|------|------|------|
| 1 | YouTube HTML 結構（ytInitialData）| ✅ 已驗證 | POC 確認可爬蟲；JSON 路徑明確 |
| 2 | 正則提取 ytInitialData JSON | ✅ 已驗證 | POC 成功提取，可靠性確認 |
| 3 | metadata 欄位完整性 | ⚠️ 部分 | video_id 100%；publish_date/view_count 可提取但非必須 |
| 4 | Redis 連線與快取策略 | ✅ 已確定 | TTL 3600 秒，使用 SHA256(keyword) 作快取鍵 |
| 5 | FastAPI + Pydantic 模型 | ✅ 標準 | 無特殊複雜性，直接應用 |
| 6 | 錯誤處理與日誌 | ✅ 已確定 | RESTful 格式 + 結構化日誌（Python logging） |
| 7 | Unicode 與特殊字符編碼 | ✅ 已驗證 | POC 成功處理「張學友 吻別」等中文 |

**結論**：所有研究主題已獲充分澄清。無需額外 Phase 0 專項研究。

## Phase 1：設計與合約

### 1. 數據模型設計

#### 實體定義（確認自規範）

**Video 模型**：

```python
class Video(BaseModel):
    video_id: str                               # 必須
    title: str | None = None                   # 最佳努力
    url: str | None = None                     # 最佳努力
    channel: str | None = None                 # 最佳努力
    channel_url: str | None = None             # 最佳努力
    publish_date: str | None = None            # 最佳努力，ISO 8601 格式
    view_count: int | None = None              # 最佳努力
    description: str | None = None             # 最佳努力
```

**SearchResult 模型**：

```python
class SearchResult(BaseModel):
    search_keyword: str
    result_count: int
    videos: list[Video]
    timestamp: str                              # ISO 8601 UTC
```

### 2. API 合約（OpenAPI）

#### 端點：GET /api/v1/search

**請求**：

```http
GET /api/v1/search?keyword=Python教學&limit=5&sort_by=relevance
```

**查詢參數**：

| 參數 | 類型 | 預設 | 範圍 | 說明 |
|------|------|------|------|------|
| keyword | string | 必須 | 1-200 字元 | 搜尋關鍵字 |
| limit | integer | 1 | 1-100 | 返回結果數量 |
| sort_by | string | relevance | relevance, date | 排序方式 |

**排序邏輯**：

- `sort_by=relevance`：保持 YouTube 預設順序（無額外排序邏輯）
- `sort_by=date`：按 `publish_date` 欄位升序排序；若 `publish_date` 缺失則該筆影片置尾

**成功回應（HTTP 200）**：

```json
{
  "search_keyword": "Python教學",
  "result_count": 5,
  "videos": [
    {
      "video_id": "abc123",
      "title": "Python 基礎教學",
      "url": "https://www.youtube.com/watch?v=abc123",
      "channel": "教學頻道",
      "channel_url": "https://www.youtube.com/c/...",
      "publish_date": "2024-01-15T10:30:00Z",
      "view_count": 50000,
      "description": "從入門到精通..."
    }
  ],
  "timestamp": "2025-12-07T12:00:00Z"
}
```

**失敗回應（HTTP 400）**：

```json
{
  "error": "keyword 長度超過 200 字元",
  "error_code": "INVALID_KEYWORD_LENGTH"
}
```

**失敗回應（HTTP 503）**：

```json
{
  "error": "YouTube 無法連接",
  "error_code": "YOUTUBE_UNAVAILABLE"
}
```

### 3. 快速啟動指南

見 `quickstart.md`（待生成）。

## Phase 2（下一步）

本計劃涵蓋至 Phase 1 完成。Task 生成、時程排期、詳細開發步驟見 `/speckit.tasks` 命令輸出。

---

**下一步**：執行 `/speckit.tasks 001-youtube-search-api` 以生成任務清單與時程表。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
