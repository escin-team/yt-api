#!/usr/bin/env bash
"""
批次下載 ZIP 功能測試腳本

此腳本演示如何使用新的批次下載 API 端點。
"""

set -e

# 設置變數
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_ENDPOINT="${API_BASE_URL}/api/v1/download/batch"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}批次下載 ZIP 功能測試${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 檢查 API 伺服器是否運行
echo -e "${YELLOW}[1/3] 檢查 API 伺服器...${NC}"
if curl -s "${API_BASE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ API 伺服器正在運行${NC}"
else
    echo -e "${RED}✗ 無法連接到 API 伺服器: ${API_BASE_URL}${NC}"
    echo "請確保 FastAPI 伺服器已啟動"
    exit 1
fi
echo ""

# 測試案例 1: 有效的影片 ID
echo -e "${YELLOW}[2/3] 測試案例 1: 下載多個有效影片${NC}"
echo "發送請求到: ${API_ENDPOINT}"
echo ""

# 使用已知的 YouTube 影片 ID
VIDEO_IDS='["dQw4w9WgXcQ", "jNQXAC9IVRw"]'
echo "影片 ID: ${VIDEO_IDS}"
echo ""

RESPONSE=$(curl -s -X POST "${API_ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d "{\"video_ids\": ${VIDEO_IDS}}")

echo "回應:"
echo "${RESPONSE}" | python3 -m json.tool 2>/dev/null || echo "${RESPONSE}"
echo ""

# 提取 ZIP URL
ZIP_URL=$(echo "${RESPONSE}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('zip_url', ''))" 2>/dev/null || echo "")

if [ -n "${ZIP_URL}" ]; then
    echo -e "${GREEN}✓ 成功獲取 ZIP 下載連結${NC}"
    echo "ZIP URL: ${ZIP_URL}"
    echo ""

    # 測試 ZIP 下載
    echo -e "${YELLOW}[3/3] 下載 ZIP 檔案...${NC}"

    # 提取 ZIP 檔名
    ZIP_FILENAME=$(basename "${ZIP_URL}")
    OUTPUT_FILE="/tmp/${ZIP_FILENAME}"

    echo "下載至: ${OUTPUT_FILE}"

    if curl -s -o "${OUTPUT_FILE}" "${ZIP_URL}"; then
        FILE_SIZE=$(ls -lh "${OUTPUT_FILE}" | awk '{print $5}')
        echo -e "${GREEN}✓ ZIP 下載成功${NC}"
        echo "檔案大小: ${FILE_SIZE}"
        echo ""

        # 驗證 ZIP 完整性
        if unzip -t "${OUTPUT_FILE}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ZIP 檔案完整性驗證成功${NC}"
            echo ""

            # 列出 ZIP 內容
            echo "ZIP 內容："
            unzip -l "${OUTPUT_FILE}"
        else
            echo -e "${RED}✗ ZIP 檔案損壞${NC}"
        fi
    else
        echo -e "${RED}✗ ZIP 下載失敗${NC}"
    fi
else
    echo -e "${RED}✗ 無法獲取 ZIP 下載連結${NC}"
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}測試完成${NC}"
echo -e "${BLUE}================================${NC}"
