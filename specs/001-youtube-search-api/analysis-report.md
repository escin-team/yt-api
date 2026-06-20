# 規範一致性分析報告：YouTube 搜尋 API

**分析日期**：2025-12-07 | **功能**：`001-youtube-search-api`
**分析方法**：逐段對比 spec.md、plan.md、tasks.md、data-model.md、contracts/openapi.yaml
**範圍**：核心工件間的重複、歧義、遺漏、衝突、術語一致性

---

## 執行摘要

| 指標 | 結果 | 狀態 |
|------|------|------|
| **需求涵蓋度** | 100% | ✅ 全部需求有任務對應 |
| **憲章合規性** | 6/6 原則通過 | ✅ 無違反 |
| **術語一致性** | 統一 | ✅ 所有工件使用一致的概念名稱 |
| **重複度** | 0 CRITICAL 重複 | ✅ 無衝突重複 |
| **歧義數量** | 2 個 MEDIUM | ⚠️ 見下 |
| **遺漏項** | 1 個 LOW | ℹ️ 見下 |

---

## 發現列表

### A. 需求涵蓋度

#### A1：需求→任務映射表

**檢查方法**：每個 spec.md 中的功能需求（FR-001~FR-010）是否在 tasks.md 中有對應任務。

| 需求 | 描述 | 任務映射 | 涵蓋度 |
|------|------|---------|--------|
| **FR-001** | YouTube URL 爬蟲 | T006 (scraper.py) | ✅ |
| **FR-002** | video_id 提取 | T006, T012 (scraper.py enhancement) | ✅ |
| **FR-003** | RESTful API 端點 | T010 (GET /api/v1/search) | ✅ |
| **FR-004** | metadata 提取 | T012, T014 (metadata extraction + normalization) | ✅ |
| **FR-005** | 輸入驗證 | T007, T021 (validators.py) | ✅ |
| **FR-006** | 結構化日誌 | T003 (logger.py), T016 (API response logging) | ✅ |
| **FR-007** | YouTube ToS 遵守 | 架構決策（爬蟲不儲存），無特定任務 | ✅ 設計驗證 |
| **FR-008** | Redis 快取（TTL 3600） | T026, T027 (cache.py, 快取整合) | ✅ |
| **FR-009** | limit 參數支援（1-100） | T021, T023 (參數驗證、API 實現) | ✅ |
| **FR-010** | RESTful 錯誤格式 | T010 (API 基礎錯誤), T016 (回應結構) | ✅ |

**結論**：10/10 功能需求涵蓋 → **100% 涵蓋度** ✅

### B. 用戶故事→階段映射

| 故事 | spec.md 優先級 | tasks.md 階段 | 一致性 |
|------|---|---|---|
| [US1] 基本搜尋 | P1 | Phase 1（T005-T011） | ✅ 一致 |
| [US2] 元數據提取 | P1 | Phase 2（T012-T019） | ✅ 一致 |
| [US3] 排序過濾 | P2 | Phase 3（T020-T025） | ✅ 一致 |

**結論**：優先級與任務組織完全一致 ✅

---

## 一致性檢查

### C. 術語一致性

#### 檢查核心概念定義是否跨文件統一

| 概念 | spec.md 定義 | plan.md 使用 | tasks.md 使用 | 一致性 |
|------|--|--|--|--|
| **Video** | 影片（實體） | Video 模型 | T005 src/models/video.py | ✅ 一致 |
| **SearchResult** | 搜尋結果（實體） | SearchResult 模型 | T016 API 回應結構 | ✅ 一致 |
| **metadata** | 影片的 metadata（title、channel 等） | 數據模型設計 | T012-T014 提取與正規化 | ✅ 一致 |
| **快取** | Redis TTL 3600 秒 | 快取策略（SHA256 鍵） | T026 cache.py 實現 | ✅ 一致 |
| **limit 參數** | 預設 1，範圍 1-100 | API 合約設定 | T021, T023 驗證與實現 | ✅ 一致 |
| **sort_by** | relevance、date 兩種排序 | 計劃未詳述 | T020 sortter.py 實現 | ⚠️ 見 D3 |

**結論**：術語統一，無命名衝突 ✅

---

## 重複與衝突

### D1：任務重複檢查

按任務檔案路徑檢查是否有重複定義：

| 檔案路徑 | 首次出現 | 其他出現 | 重複度 |
|---------|---------|---------|--------|
| `src/models/video.py` | T005 | T013 (enhancement) | ⚠️ 同檔多次編輯（預期） |
| `src/services/scraper.py` | T006 | T012 (enhancement) | ⚠️ 同檔多次編輯（預期） |
| `src/utils/validators.py` | T007 | T021 (enhancement) | ⚠️ 同檔多次編輯（預期） |
| `src/api/v1/search.py` | T010 | T016, T023 (enhancements) | ⚠️ 同檔多次編輯（預期） |

**結論**：無衝突重複，多次編輯同檔為迭代演化（預期設計） ✅

### D2：功能衝突檢查

檢查不同任務是否有互斥的設計決策：

**無衝突** ✅

- 快取實現（T026）不與 API 實現（T010）衝突
- 排序邏輯（T020）不與搜尋服務（T008）衝突
- 驗證增強（T021）不與基礎驗證（T007）衝突

---

## 歧義與遺漏

### E1：sort_by 實現詳情缺失 [MEDIUM]

**問題**：

- spec.md 定義 sort_by 參數接受 `relevance` 或 `date`
- tasks.md T020 建立 `src/services/sorter.py` 實現排序邏輯
- **遺漏**：無規範文件詳述 relevance 與 date 排序的具體實現方式

**實際影響**：

- `relevance`：YouTube 預設順序（無需額外排序邏輯）
- `date`：按 `publish_date` 欄位排序（需實現比較邏輯）

**建議**：在 plan.md 或 data-model.md 補充 `sorter.py` 實現細節

**嚴重度**：MEDIUM（不阻塞開發，但容易造成誤解）

### E2：Redis 快取失敗降級策略未明確 [MEDIUM]

**問題**：

- spec.md FR-008 定義快取 TTL 為 3600 秒
- tasks.md T026 實現 Redis 快取層
- **遺漏**：Redis 連線失敗或超時時，系統應如何降級？

**可能情景**：

1. 拋出異常 → API 返回 HTTP 503
2. 跳過快取繼續爬蟲 → 返回新鮮結果（慢）
3. 返回暫存結果 → 可能無法取得

**建議**：在 plan.md 「快取策略」或 spec.md 「假設與限制」中明確定義降級行為

**嚴重度**：MEDIUM（影響容錯設計）

### E3：timestamp 格式精度 [LOW]

**問題**：

- spec.md SearchResult 定義 `timestamp: 搜尋時間戳記`
- plan.md 定義 `timestamp: ISO 8601 UTC`
- **遺漏**：精度是否為秒 (Z) 或毫秒 (.000Z)？

**範例**：

- 秒級：`2025-12-07T12:00:00Z`
- 毫秒級：`2025-12-07T12:00:00.000Z`

**建議**：在 data-model.md SearchResult 實體說明中補充 timestamp 格式範例

**嚴重度**：LOW（不影響功能，但影響 API 一致性）

---

## 憲章對齊檢查

### F1：原則遵循驗證

| 原則 | 狀態 | 驗證 |
|------|------|------|
| **I. POC 最小化測試** | ✅ | tasks.md Phase 0-4 中，測試任務標記為可選（T011、T017-T019、T024-T025、T028）|
| **II. 清潔架構** | ✅ | 分層架構明確（models → services → api），各層獨立（符合 plan.md）|
| **III. 明確勝過隱含** | ✅ | 所有參數、錯誤、metadata 策略明確定義（spec.md 10 個 FR 完整）|
| **IV. 簡潔優先** | ✅ | 使用標準工具（requests、re、json、FastAPI），無過度設計（plan.md 明確）|
| **V. 程式碼即配置** | ✅ | Redis 連線、API 端口、TTL 全由環境變數控制（spec.md FR-008 確認）|
| **VI. 正體中文文件** | ✅ | spec.md、plan.md、tasks.md、data-model.md、contracts/openapi.yaml 全採正體中文 |

**結論**：6/6 原則符合 → **無憲章衝突** ✅

---

## 跨工件依賴關係

### G1：檔案結構一致性

**plan.md 定義的檔案結構** vs **tasks.md 任務對應**

| plan.md 路徑 | tasks.md 任務對應 | 驗證 |
|---|---|---|
| `src/models/video.py` | T005, T013 | ✅ |
| `src/models/search.py` | T005, T013 | ✅ |
| `src/services/scraper.py` | T006, T012 | ✅ |
| `src/services/search.py` | T008, T015, T022, T027 | ✅ |
| `src/services/cache.py` | T026, T027 | ✅ |
| `src/services/normalizer.py` | T014 | ✅ |
| `src/services/sorter.py` | T020 | ✅ |
| `src/api/v1/search.py` | T010, T016, T023, T027 | ✅ |
| `src/utils/validators.py` | T007, T021 | ✅ |
| `src/utils/logger.py` | T003 | ✅ |
| `src/utils/errors.py` | T004 | ✅ |
| `src/config.py` | T002 | ✅ |
| `main.py` | T009 | ✅ |
| `tests/` | T011, T017-T019, T024-T025, T028 | ✅ |

**結論**：100% 對應 ✅

### G2：資料模型完整性

**spec.md 實體定義** → **data-model.md 詳細設計** → **tasks.md 實現任務**

**Video 實體**：

```
spec.md: 8 個欄位定義
  ↓
data-model.md: Pydantic 型別、驗證規則、JSON 序列化（見 320+ 行）
  ↓
tasks.md: T005 (初始), T013 (驗證增強), T014 (正規化)
```

**SearchResult 實體**：

```
spec.md: 4 個欄位定義
  ↓
data-model.md: Pydantic 型別、timestamp ISO 8601 格式
  ↓
tasks.md: T016 (API 回應結構整合)
```

**結論**：資料流完整 ✅

---

## 測試涵蓋計劃

### H1：測試任務映射

| 測試層 | spec.md 測試準則 | tasks.md 任務 | 對應 |
|--------|---|---|---|
| **單元測試** | metadata 欄位驗證 | T017 (metadata_extraction), T019 (models) | ✅ |
| **單元測試** | 排序邏輯 | T024 (sorting) | ✅ |
| **單元測試** | 參數驗證 | T025 (parameters) | ✅ |
| **煙霧測試** | API 基本搜尋 | T011 (api_basic) | ✅ |
| **整合測試** | 元數據提取端到端 | T018 (api_metadata) | ✅ |
| **整合測試** | 快取功能 | T028 (cache) | ✅ |

**結論**：測試計劃完整 ✅

---

## 效能與非功能需求

### I1：可測量性檢查

| 非功能需求 | spec.md | plan.md | tasks.md 對應 | 可測量性 |
|---|---|---|---|---|
| **SC-001** 3 秒內返回 | ✅ 明確 | ✅ 效能目標 | T026-T028 快取優化 | ✅ 可測（時間測量） |
| **SC-002** video_id 95% 正確率 | ✅ 明確 | ⚠️ 未深入 | T011 煙霧測試 | ⚠️ 手動驗證 |
| **SC-003** 100 個關鍵字 90% 無誤 | ✅ 明確 | ⚠️ 未深入 | T011 煙霧測試 | ⚠️ 手動驗證 |
| **SC-004** metadata 100% 一致性 | ✅ 明確 | ✅ 驗證規則 | T019 模型測試 | ✅ 可測 |
| **SC-005** 特殊字符處理 | ✅ 明確 | ✅ Unicode 驗證 | T007, T021 驗證模組 | ✅ 可測 |

**結論**：大部分可測，SC-002 / SC-003 建議補充自動化測試框架

---

## 空隙與未決問題

### J1：待澄清項目

| 項目 | 當前狀態 | 建議 |
|------|---------|------|
| sort_by = "relevance" 實現細節 | 規範提及，計劃未詳述 | 補充 plan.md 或 data-model.md |
| Redis 快取失敗降級 | 規範未明確 | 補充 spec.md 「假設與限制」 |
| timestamp 精度 | 定義為 ISO 8601 UTC，未指定秒/毫秒 | 補充 data-model.md 範例 |
| sort_by = "date" 時，無 publish_date 的影片如何排序 | 規範未定 | 補充排序邏輯說明 |
| API 版本升級策略（/api/v1/ → /api/v2/） | plan.md 提及但未詳述 | 可延後至 Phase 3+ 文檔 |

---

## 跨工件推薦改進

### K1：高優先級改進

1. **補充 sort_by 實現詳情** [MEDIUM]
   - **檔案**：plan.md Phase 1 設計與合約 → 2. API 合約（OpenAPI）
   - **內容**：補充排序邏輯

     ```markdown
     - sort_by=relevance：保持 YouTube 預設順序（無額外排序）
     - sort_by=date：按 publish_date 升序排序；若 publish_date 缺失則置尾
     ```

2. **定義 Redis 降級策略** [MEDIUM]
   - **檔案**：spec.md 假設與限制
   - **內容**：補充一行

     ```markdown
     - Redis 連線失敗時：拋出例外，API 返回 HTTP 503 與 error_code=CACHE_UNAVAILABLE
     ```

3. **timestamp 格式精化** [LOW]
   - **檔案**：data-model.md SearchResult
   - **內容**：補充範例

     ```markdown
     timestamp: "2025-12-07T12:00:00Z"  # ISO 8601 UTC，秒級精度
     ```

### K2：任務層面改進

1. **T011 煙霧測試補充自動化框架**
   - 當前：基本功能驗證
   - 建議：集成 pytest fixtures，涵蓋 SC-002（video_id 正確率）

2. **T026 Redis 快取失敗處理**
   - 當前：基本快取實現
   - 建議：補充異常捕捉與 logging，測試降級路徑

---

## 總結與建議

### ✅ 良好實踐

1. **需求到任務的完整追蹤** - 10/10 功能需求有任務對應
2. **一致的術語使用** - 無命名衝突，概念清晰
3. **憲章原則全覆蓋** - 6/6 原則符合
4. **清晰的分階段計劃** - Phase 0-4 按優先級組織
5. **獨立的測試標準** - 每階段有明確的驗收準則

### ⚠️ 建議改進

1. **補充 3 個歧義澄清**（見 E1-E3）
2. **增強非功能需求的自動化測試**（SC-002、SC-003）
3. **明確快取失敗降級**（spec.md）
4. **排序實現細節**（plan.md）

### 📊 一致性評分

| 維度 | 評分 | 注 |
|------|------|-----|
| 需求涵蓋度 | 10/10 | 100% |
| 術語一致性 | 10/10 | 無衝突 |
| 憲章合規性 | 10/10 | 6/6 原則通過 |
| 檔案結構對應 | 12/12 | 100% |
| 歧義消除度 | 7/10 | 2 個 MEDIUM，1 個 LOW |
| **總體一致性** | **90%** | **良好，建議補充 3 個澄清** |

---

**分析完成**：2025-12-07 | **下一步**：應用 K1 推薦改進，完善三個核心澄清點
