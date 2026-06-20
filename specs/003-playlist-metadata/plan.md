# Implementation Plan: YouTube 播放列表元數據提取

**Branch**: `003-playlist-metadata` | **Date**: 2025-12-08 | **Spec**: `/specs/003-playlist-metadata/spec.md`
**Input**: Feature specification from `/specs/003-playlist-metadata/spec.md`

**Language**: 本文件與所有 `/speckit` 產出（plan/spec/tasks/checklist 等）必須使用正體中文撰寫

**Note**: 此計畫依 `/speckit.plan` 工作流程產出，後續 Phase 0/1 產物需保持同步更新。

## Summary

新增 FastAPI 端點處理播放列表 URL，從 `list=` 參數解析播放列表 ID，透過網頁爬取 (ytInitialData/HTML) 取得所有曲目的 `title`（必填）及 `video_id`、`channel`、`url`、`publish_date`、`duration` 等可用欄位，一次性回傳完整清單，並以 Redis 快取結果（TTL 由 `REDIS_TTL_SECONDS` 控制）避免重複爬取，嚴禁使用 YouTube Data API。

## Technical Context

**Language/Version**: Python 3.12 (pyproject 要求 >=3.12)
**Primary Dependencies**: FastAPI、Pydantic、requests、anyio、redis；HTML/JSON 解析沿用 ytInitialData 抽取與 `continuation` token 迭代，不新增額外解析套件
**Storage**: Redis 快取（`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`、`REDIS_TTL_SECONDS` 配置，預設 TTL 3600 秒）
**Testing**: pytest 可用，但依憲章以最小 smoke 測試與手動驗證為主；需覆蓋基本 API 成功與錯誤碼分支
**Target Platform**: Linux/macOS 伺服器，uvicorn/FastAPI 運行
**Project Type**: 後端 API（FastAPI 路由 + Service 層）
**Performance Goals**: 50 首播放列表處理時間 ≤ 30 秒；快取命中延遲 ≤ 500ms；支援 ≥100 併發請求
**Constraints**: 嚴禁呼叫 YouTube Data API（googleapis.com），僅允許 youtube.com 爬取；需從 playlist HTML/ytInitialData 抽取 metadata；需區分 400/403/404/410/502 錯誤並遵循結構化錯誤格式（code/message/reason/trace_id）；長列表以 `continuation` 迭代且設置批次上限（建議 ≤15 批）與總超時（≤30s），超過時標記 `partial=true` 並回傳已取得結果
**Scale/Scope**: 針對使用者一次性回傳完整列表，不支援分頁；預期 playlist 可達數百至上千首曲目；超長列表允許 partial 回應以避免超時

## Constitution Check

*GATE: 必須在 Phase 0 研究前成立，Phase 1 設計後需再次檢視。*

- 文件語系：所有計畫/研究/設計輸出均以正體中文撰寫（符合 VI）。
- 減量測試：POC 階段可僅 smoke/手動驗證，但需紀錄驗證結果，不得使用 skip 隱藏問題（符合 I）。
- 架構：維持 Service/Model/Router 分層，依賴注入顯式化；不得引入隱式全域狀態（符合 II、III）。
- 設定與安全：設定來源為環境變數與 pydantic-settings；使用集中 logger；錯誤訊息需明確且不洩漏敏感資訊（符合 III、V）。
- API 合規：禁止使用 YouTube Data API，僅允許網頁爬取 youtube.com（符合 V）。

目前無已知憲章違反；Phase 0 研究已確認解析策略與長列表處理方案。

Phase 1 覆核：設計維持 Service/Router 分層與環境設定顯式配置，新增的快取與 partial 回應策略皆符合憲章，無需豁免。

## Project Structure

### Documentation (this feature)

```text
specs/003-playlist-metadata/
├── plan.md              # 本檔案
├── research.md          # Phase 0 研究輸出
├── data-model.md        # Phase 1 實體與欄位設計
├── quickstart.md        # Phase 1 操作指南
├── contracts/           # Phase 1 API 契約（OpenAPI/GraphQL 等）
└── tasks.md             # Phase 2 (/speckit.tasks 產出，非本階段)
```

### Source Code (repository root)

```text
src/
└── youtube_search/
    ├── api/v1/
    │   └── search.py              # 現有搜尋端點，新增播放列表端點將放此層
    ├── services/
    │   ├── search.py              # 搜尋協調服務，可類比新增 playlist 服務
    │   ├── scraper.py             # 既有搜尋爬蟲，需擴充播放列表爬取邏輯
    │   ├── cache.py               # Redis 快取封裝
    │   ├── normalizer.py          # 中介資料正規化
    │   └── sorter.py              # 排序工具（可能重用）
    ├── models/
    │   ├── search.py              # SearchResult 模型，可參考建立 PlaylistResult
    │   └── video.py               # Video/metadata 模型，需檢視是否延用或擴充
    └── utils/
        ├── errors.py             # 統一錯誤型別與狀態碼
        └── validators.py         # 驗證工具，可新增 playlist URL/ID 驗證

tests/
├── integration/                  # 端點與服務整合測試
└── unit/                         # 單元測試（依憲章可最小化）
```

**Structure Decision**: 延用單一後端專案結構（FastAPI + Service 分層）；新播放列表端點與服務將與現有 search API 並列，重用 utils/models/redis 設定，避免新增額外專案或前端模組。

## Complexity Tracking

目前無需額外複雜度豁免；如後續需要分批抓取或引入新解析庫，再評估是否新增條目。
