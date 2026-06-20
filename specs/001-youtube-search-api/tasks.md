# 任務清單與時程表：YouTube 搜尋 API

**功能名稱**：`001-youtube-search-api` | **分支**：`001-youtube-search-api`
**建立日期**：2025-12-07 | **目標平台**：Python 3.12+、FastAPI、Redis
**生成方式**：遵循 speckit.tasks 工作流（plan.md + spec.md + data-model.md + contracts/openapi.yaml）

**語言**：本文件與所有產出必須使用正體中文撰寫

---

## 概述

本任務清單按用戶故事優先級分階段組織，每個故事獨立實現與測試。建議 MVP 範圍為 **Phase 1-2**（核心搜尋 + metadata 提取），Phase 3 作為後續迭代。

| 階段 | 標題 | 用戶故事 | 任務數 | 承諾 |
|------|------|---------|--------|------|
| **Phase 0** | 環境與基礎設置 | - | 4 | 設置開發環境、專案結構 |
| **Phase 1** | 基本搜尋功能 | [US1] | 7 | 爬蟲層、搜尋服務、API 端點 |
| **Phase 2** | 元數據提取 | [US2] | 8 | 數據模型、提取邏輯、驗證 |
| **Phase 3** | 排序與過濾 | [US3] | 6 | 排序邏輯、limit 參數、快取最佳化 |
| **Phase 4** | 優化與部署 | - | 4 | 效能、日誌、文檔、容器化 |

**推薦 MVP**：Phase 1 + Phase 2（可獨立驗證）

---

## Phase 0：環境與基礎設置

### 目標

設置開發環境、初始化專案結構、配置工具鏈。

### 獨立測試標準

- ✅ 專案結構按 plan.md 建立完整
- ✅ `uv sync` 安裝所有依賴無誤
- ✅ `pytest` 可執行，測試框架可用
- ✅ `.env` 配置可載入，無缺失必要變數

### 實作任務

- [X] **T001** 初始化 Python 套件結構 (`src/__init__.py` 及子模組) - `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/api/__init__.py`, `src/utils/__init__.py`
- [X] **T002** 建立環境配置檔案 `.env.example` 與 `src/config.py` - `src/config.py`, `.env.example`
- [X] **T003** 建立日誌模組 `src/utils/logger.py` - `src/utils/logger.py`
- [X] **T004** 建立自訂例外模組 `src/utils/errors.py` - `src/utils/errors.py`

---

## Phase 1：基本搜尋功能 [US1]

### 故事目標

系統提供 API 端點接受關鍵字輸入，透過 YouTube 搜尋結果頁面取得符合的影片清單。

### 獨立測試標準

- ✅ `GET /api/v1/search?keyword=Python教學` 返回 HTTP 200
- ✅ 回應包含 `videos` 陣列，至少一筆記錄
- ✅ 每筆記錄都包含 `video_id`
- ✅ 搜尋結果一致性：同一關鍵字多次呼叫結果相同（若無快取）

### 實作任務

- [X] **T005** [P] 建立 Pydantic 基礎模型 `src/models/video.py` 和 `src/models/search.py` - `src/models/video.py`, `src/models/search.py`
- [X] **T006** [P] 建立 YouTube 爬蟲服務 `src/services/scraper.py` (HTML 解析、正則提取 video_id) - `src/services/scraper.py`
- [X] **T007** [P] 建立輸入驗證模組 `src/utils/validators.py` (keyword 驗證) - `src/utils/validators.py`
- [X] **T008** [P] [US1] 建立搜尋協調服務 `src/services/search.py` (爬蟲 + 模型整合) - `src/services/search.py`
- [X] **T009** [US1] 建立 FastAPI 應用入口 `main.py` 與 API v1 基礎 - `main.py`, `src/api/v1/__init__.py`, `src/api/v1/search.py`
- [X] **T010** [US1] 實現 GET `/api/v1/search` 端點 (keyword 參數、基礎錯誤處理) - `src/api/v1/search.py`
- [X] **T011** [US1] 編寫 Phase 1 煙霧測試 `tests/test_api_basic.py` (搜尋功能基本驗證) - `tests/test_api_basic.py`

---

## Phase 2：元數據提取 [US2]

### 故事目標

API 從搜尋結果中提取並整理各影片的 metadata，包括 video_id、標題、描述、頻道、發佈日期等，以標準化格式返回。

### 獨立測試標準

- ✅ 每筆搜尋結果都包含預期 metadata（video_id、title、channel、url）
- ✅ metadata 格式一致（無雜亂資料）
- ✅ 可選欄位提取成功率 ≥ 50%（publish_date、view_count、description）
- ✅ 可選欄位提取失敗時正確設為 null（非空字符串或異常）

### 實作任務

- [X] **T012** [P] [US2] 增強爬蟲提取邏輯 (title、channel、url、publish_date、view_count、description) - `src/services/scraper.py`
- [X] **T013** [P] [US2] 完善 Pydantic 模型驗證規則 (欄位型別、可選性、邊界) - `src/models/video.py`, `src/models/search.py`
- [X] **T014** [P] [US2] 建立 metadata 正規化服務 `src/services/normalizer.py` (null 容錯、格式一致化) - `src/services/normalizer.py`
- [X] **T015** [US2] 整合 metadata 提取至搜尋服務 - `src/services/search.py`
- [X] **T016** [US2] 增強 API 回應結構 (SearchResult、timestamp、result_count) - `src/api/v1/search.py`
- [X] **T017** [US2] 編寫 metadata 提取單元測試 `tests/unit/test_metadata_extraction.py` - `tests/unit/test_metadata_extraction.py`
- [X] **T018** [US2] 編寫 API metadata 整合測試 `tests/integration/test_api_metadata.py` - `tests/integration/test_api_metadata.py`
- [X] **T019** [US2] 編寫 Pydantic 模型驗證測試 `tests/unit/test_models.py` - `tests/unit/test_models.py`

---

## Phase 3：排序與過濾 [US3]

### 故事目標

API 支援根據相關性、發佈日期或觀看數對結果進行排序，允許客戶端指定返回的影片數量上限。

### 獨立測試標準

- ✅ `limit=5` 返回最多 5 筆結果
- ✅ `sort_by=relevance` 按相關性排序
- ✅ `sort_by=date` 按發佈日期排序
- ✅ `limit` 超過 100 時返回 HTTP 400
- ✅ 預設 limit=1 返回 1 筆結果

### 實作任務

- [X] **T020** [P] [US3] 實現結果排序邏輯 `src/services/sorter.py` (relevance、date) - `src/services/sorter.py`
- [X] **T021** [P] [US3] 增強驗證模組支援 limit 與 sort_by 參數 - `src/utils/validators.py`
- [X] **T022** [US3] 更新搜尋服務整合排序邏輯 - `src/services/search.py`
- [X] **T023** [US3] 更新 API 端點實現 limit 與 sort_by 參數 - `src/api/v1/search.py`
- [X] **T024** [US3] 編寫排序與過濾單元測試 `tests/unit/test_sorting.py` - `tests/unit/test_sorting.py`
- [X] **T025** [US3] 編寫 limit 邊界情況測試 `tests/unit/test_parameters.py` - `tests/unit/test_parameters.py`

---

## Phase 4：優化與部署

### 目標

實現快取、效能優化、完整日誌、容器化與文檔。

### 獨立測試標準

- ✅ 同一關鍵字快取命中（第二次查詢 < 100ms）
- ✅ 搜尋延遲 ≤ 3 秒（含網路）
- ✅ 日誌包含所有要求追蹤資訊
- ✅ Docker 鏡像構建與執行無誤

### 實作任務

- [X] **T026** [P] 實現 Redis 快取層 `src/services/cache.py` (TTL、SHA256 鍵生成、失敗時拋出例外不降級) - `src/services/cache.py`
- [X] **T027** [P] 整合快取至搜尋服務與 API 層 - `src/services/search.py`, `src/api/v1/search.py`
- [X] **T028** [P] 編寫快取整合測試 `tests/integration/test_cache.py` - `tests/integration/test_cache.py`
- [X] **T029** 建立 Dockerfile 與 docker-compose.yml 配置 - `Dockerfile`, `docker-compose.yml`

---

## 依賴關係與執行順序

### 故事依賴圖

```
Phase 0 (基礎)
    ↓
Phase 1 [US1]：基本搜尋
    ↓
Phase 2 [US2]：元數據提取（可並行 T012-T015）
    ↓
Phase 3 [US3]：排序過濾（可並行 T020-T025）
    ↓
Phase 4：優化部署
```

### 關鍵阻塞點

1. **T001-T004 必須完成** 才能開始任何服務開發（Phase 1）
2. **T005-T007 可並行** 建立模型與爬蟲（獨立模組）
3. **T008-T010 依賴 T005-T007 完成** 後進行整合
4. **T012-T019 依賴 Phase 1 完成** 但 T012-T014 可在 T010 後立即並行
5. **T020-T025 完全獨立於 Phase 2** 可在 Phase 1 完成後並行進行
6. **T026-T028 可在 Phase 1 完成後任何時刻進行** 無數據依賴

### 並行執行範例

**場景 A：快速 MVP（2 天）**

- **Day 1**：T001-T010（環境 + 基本搜尋）→ 快速驗證爬蟲可行性
- **Day 2**：T012-T019（元數據）→ 完整結果返回

**場景 B：完整 Phase 1-3（4 天）**

- **Day 1**：T001-T010（基礎 + 搜尋）
- **Day 2**：T012-T025（metadata + 排序，分兩個開發者並行）
- **Day 3-4**：T026-T029（快取、測試、部署）

---

## 實作策略

### MVP 優先（推薦）

**範圍**：Phase 1 + Phase 2
**預期產出**：

- ✅ 完整搜尋 API（keyword 必須，limit 預設 1，無排序）
- ✅ 所有 metadata 提取（video_id 必須，其他最佳努力 + null）
- ✅ 基礎錯誤處理（keyword 驗證、YouTube 失敗 503）
- ✅ 煙霧測試驗證功能可用性
- **未包含**：快取、排序、生產部署

**時間估算**：3-4 天（2 人開發）

### 完整 Phase 1-3

**範圍**：MVP + Phase 3
**額外產出**：

- ✅ 排序與過濾（sort_by、limit 1-100）
- ✅ 完整單元測試
- **未包含**：快取、容器化

**時間估算**：4-5 天

### 生產就緒

**範圍**：Phase 1-4
**額外產出**：

- ✅ Redis 快取（TTL 3600 秒）
- ✅ 完整整合測試
- ✅ 結構化日誌
- ✅ Docker 部署

**時間估算**：6-7 天

---

## 檢查點與驗收

### Phase 1 完成時

- [ ] API 能回應有效搜尋請求（HTTP 200）
- [ ] 回應包含 video_id 欄位
- [ ] 至少 3 個不同關鍵字測試通過
- [ ] 無未捕捉異常

### Phase 2 完成時

- [ ] 所有 metadata 欄位按 spec 返回（必須 vs 最佳努力明確）
- [ ] 可選欄位失敗時正確設為 null
- [ ] Pydantic 驗證通過（型別、範圍一致）
- [ ] 單元測試覆蓋 ≥ 70%

### Phase 3 完成時

- [ ] limit 參數運作正確（1-100）
- [ ] sort_by 兩種排序選項可用
- [ ] 邊界情況返回 HTTP 400（超出 limit）
- [ ] 整合測試通過

### Phase 4 完成時

- [ ] Redis 快取命中率 > 50%（同一關鍵字重複查詢）
- [ ] 搜尋延遲 ≤ 3 秒
- [ ] Docker 鏡像成功構建並可執行
- [ ] 文檔完整（API、環境、部署）

---

## 附錄：任務 ID 對應表

| 階段 | 任務 ID | 標題 | 關聯故事 | 檔案路徑 |
|------|--------|------|---------|---------|
| P0 | T001 | 初始化套件結構 | - | `src/**/__init__.py` |
| P0 | T002 | 環境配置 | - | `src/config.py`, `.env.example` |
| P0 | T003 | 日誌模組 | - | `src/utils/logger.py` |
| P0 | T004 | 例外模組 | - | `src/utils/errors.py` |
| P1 | T005 | 數據模型 | [US1] | `src/models/*.py` |
| P1 | T006 | 爬蟲服務 | [US1] | `src/services/scraper.py` |
| P1 | T007 | 驗證模組 | [US1] | `src/utils/validators.py` |
| P1 | T008 | 搜尋服務 | [US1] | `src/services/search.py` |
| P1 | T009 | FastAPI 應用 | [US1] | `main.py`, `src/api/v1/__init__.py` |
| P1 | T010 | API 搜尋端點 | [US1] | `src/api/v1/search.py` |
| P1 | T011 | 煙霧測試 | [US1] | `tests/test_api_basic.py` |
| P2 | T012 | 增強爬蟲 | [US2] | `src/services/scraper.py` |
| P2 | T013 | 完善模型驗證 | [US2] | `src/models/*.py` |
| P2 | T014 | Metadata 正規化 | [US2] | `src/services/normalizer.py` |
| P2 | T015 | 搜尋服務整合 | [US2] | `src/services/search.py` |
| P2 | T016 | API 回應結構 | [US2] | `src/api/v1/search.py` |
| P2 | T017 | Metadata 單元測試 | [US2] | `tests/unit/test_metadata_extraction.py` |
| P2 | T018 | API 整合測試 | [US2] | `tests/integration/test_api_metadata.py` |
| P2 | T019 | 模型驗證測試 | [US2] | `tests/unit/test_models.py` |
| P3 | T020 | 排序邏輯 | [US3] | `src/services/sorter.py` |
| P3 | T021 | 參數驗證增強 | [US3] | `src/utils/validators.py` |
| P3 | T022 | 排序整合 | [US3] | `src/services/search.py` |
| P3 | T023 | API 參數實現 | [US3] | `src/api/v1/search.py` |
| P3 | T024 | 排序單元測試 | [US3] | `tests/unit/test_sorting.py` |
| P3 | T025 | 參數邊界測試 | [US3] | `tests/unit/test_parameters.py` |
| P4 | T026 | Redis 快取層 | - | `src/services/cache.py` |
| P4 | T027 | 快取整合 | - | `src/services/search.py`, `src/api/v1/search.py` |
| P4 | T028 | 快取測試 | - | `tests/integration/test_cache.py` |
| P4 | T029 | 容器化 | - | `Dockerfile`, `docker-compose.yml` |

---

**建立者**：speckit.tasks | **完成狀態**：待執行 | **下一步**：從 Phase 0 T001 開始實作
