#!/bin/bash

# 用法：./run_docker.sh [command] [options]
#
# 命令：
#   up          - 啟動容器（後台）
#   down        - 停止並移除容器
#   restart     - 重啟容器
#   pull        - 從 Docker Hub 拉取鏡像
#   logs        - 查看容器日誌
#   shell       - 進入容器 shell
#   clean       - 清理所有 Docker 資源
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# 預設環境文件
ENV_FILE="${SCRIPT_DIR}/.env.docker"

# Docker 鏡像和容器名稱
IMAGE_NAME="sacahan/ytsearch:latest"
CONTAINER_NAME="ytsearch"
HOST_PORT="8441"

# Docker 網路名稱
NETWORK_NAME="sacahan-network"

# 日誌和輸出目錄
LOGS_DIR="${SCRIPT_DIR}/logs"
OUTPUT_DIR="${SCRIPT_DIR}/output"

# 確保 Docker 網路存在
ensure_network() {
	if ! docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
		echo -e "${BLUE}📡 建立 Docker 網路: $NETWORK_NAME${NC}"
		docker network create "$NETWORK_NAME"
		echo -e "${GREEN}✓ Docker 網路已建立${NC}"
	fi
}

# 檢查 .env.docker 是否存在
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  未找到 $ENV_FILE${NC}"
        echo -e "${YELLOW}正在從示例複製...${NC}"
        if [ -f "${SCRIPT_DIR}/.env.docker.example" ]; then
            cp "${SCRIPT_DIR}/.env.docker.example" "$ENV_FILE"
            echo -e "${GREEN}✓ 已建立 $ENV_FILE (請編輯後再執行)${NC}"
            echo -e "${YELLOW}請編輯 .env.docker 檔案配置必要的環境變數${NC}"
            exit 1
        else
            echo -e "${RED}✗ 找不到 .env.docker.example${NC}"
            exit 1
        fi
    fi
}

# 啟動後端容器
start_container() {
    ensure_network
    check_env_file

    # 確保目錄存在
    mkdir -p "$LOGS_DIR" "$OUTPUT_DIR"

    # 檢查是否已運行
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}ℹ️ 容器已在運行${NC}"
        return 0
    fi

    # 檢查是否存在但未運行
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${BLUE}啟動現有容器...${NC}"
        docker start "$CONTAINER_NAME"
        show_info
        return 0
    fi

    echo -e "${BLUE}🚀 啟動容器...${NC}"

    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        -p "${HOST_PORT}:8000" \
        --env-file "$ENV_FILE" \
        -v "${LOGS_DIR}:/app/logs" \
        -v "${OUTPUT_DIR}:/app/output" \
        -e TZ=Asia/Taipei \
        --restart unless-stopped \
        "$IMAGE_NAME"

    echo -e "${GREEN}✓ 容器已啟動${NC}"
    echo ""
    show_info
}

# 停止容器
stop_container() {
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}ℹ️  容器不存在${NC}"
        return 0
    fi

    echo -e "${BLUE}🛑 停止 容器...${NC}"
    docker stop "$CONTAINER_NAME"
    echo -e "${GREEN}✓ 容器已停止${NC}"
}

# 重啟容器
restart_container() {
    echo -e "${BLUE}🔄 重啟容器...${NC}"

    # 檢查容器是否存在
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}ℹ️  容器不存在，正在啟動新容器...${NC}"
        start_container
        return
    fi

    # 停止現有容器
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${BLUE}🛑 停止現有容器...${NC}"
        docker stop "$CONTAINER_NAME"
    fi

    # 移除舊容器
    docker rm "$CONTAINER_NAME" 2>/dev/null || true

    # 啟動新容器
    echo ""
    start_container
}

# 拉取 Docker 鏡像
pull_image() {
    echo -e "${BLUE}📥 從 Docker Hub 拉取鏡像: $IMAGE_NAME${NC}"

    if docker pull "$IMAGE_NAME"; then
        echo -e "${GREEN}✓ 鏡像拉取成功${NC}"
        echo ""
        echo -e "${BLUE}💡 下一步:${NC}"
        echo -e "   使用 ${GREEN}./run_docker.sh up${NC} 啟動容器"
    else
        echo -e "${RED}✗ 鏡像拉取失敗${NC}"
        echo -e "${YELLOW}請確保:${NC}"
        echo "   1. Docker 已安裝並運行"
        echo "   2. 網路連接正常"
        echo "   3. 有足夠的磁碟空間"
        exit 1
    fi
}

# 查看日誌
show_logs() {
    local type=${1:-app}

    case "$type" in
        docker|container)
            echo -e "${BLUE}📋 顯示容器日誌（按 Ctrl+C 退出）...${NC}"
            docker logs -f "$CONTAINER_NAME"
            ;;
        app|file|*)
            # 查看應用日誌文件
            if [ ! -d "$LOGS_DIR" ]; then
                echo -e "${YELLOW}⚠️  日誌目錄不存在: $LOGS_DIR${NC}"
                echo -e "${YELLOW}提示: 啟動容器後日誌文件會自動創建${NC}"
                return 1
            fi

            local log_files=("$LOGS_DIR"/youtube_search_*.log)

            if [ ! -e "${log_files[0]}" ]; then
                echo -e "${YELLOW}⚠️  未找到應用日誌文件${NC}"
                echo -e "${YELLOW}提示: 啟動容器後日誌文件會自動創建${NC}"
                return 1
            fi

            echo -e "${BLUE}📄 可用的日誌文件：${NC}"
            ls -lh "$LOGS_DIR"/youtube_search_*.log
            echo ""

            # 找到最新的日誌文件
            local latest_log=$(ls -t "$LOGS_DIR"/youtube_search_*.log | head -1)
            echo -e "${BLUE}📋 查看應用日誌: $(basename "$latest_log")${NC}"
            echo -e "${BLUE}   (按 Ctrl+C 退出)${NC}"
            echo ""
            tail -f "$latest_log"
            ;;
    esac
}

# 進入容器 shell
enter_shell() {
    local container=$1

    if [ -z "$container" ]; then
        container="$CONTAINER_NAME"
    fi

    echo -e "${BLUE}🐚 進入 $container 容器...${NC}"
    docker exec -it "$container" /bin/bash
}

# 移除容器
remove_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${BLUE}移除 容器...${NC}"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME"
    fi
}

# 清理資源
clean_up() {
    echo -e "${YELLOW}⚠️  此操作將刪除所有容器、鏡像和卷...${NC}"
    read -p "確認要繼續嗎？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}清理中...${NC}"

        # 停止並移除容器
        remove_container

        # 移除鏡像
        docker rmi "$IMAGE_NAME" 2>/dev/null || true

        # 系統清理
        docker system prune -f

        echo -e "${GREEN}✓ 清理完成${NC}"
    else
        echo -e "${YELLOW}已取消${NC}"
    fi
}

# 顯示幫助信息
show_help() {
    cat <<'EOF'
YTSearch Docker 執行腳本

用法: ./run_docker.sh [command]

📋 命令:

  up         啟動容器
  down       停止並移除容器
  restart    重啟容器
  pull       拉取鏡像
  logs       查看應用日誌文件（預設）
             logs docker  - 查看容器日誌
             logs app     - 查看應用日誌文件
  shell      進入容器 shell
  info       服務信息
  clean      清理資源
  help       顯示此幫助信息

🚀 快速開始:

  1. 拉取鏡像:
     ./run_docker.sh pull

  2. 啟動服務:
     ./run_docker.sh up

  3. 查看日誌:
     ./run_docker.sh logs          # 應用日誌（預設）
     ./run_docker.sh logs docker   # 容器日誌

  4. 停止並移除服務:
     ./run_docker.sh down

🔗 服務端點:
  Web UI:    http://localhost:8441
  API:       http://localhost:8441/api
  健康檢查:  http://localhost:8441/health

📝 環境配置:
  配置文件: .env.docker
  日誌目錄: logs/ (應用日誌: youtube_search_YYYYMMDD.log)
  輸出目錄: output/

💡 更多幫助: ./run_docker.sh info

EOF
}

# 顯示服務信息
show_info() {
    echo -e "${BLUE}📊 YTSearch 服務信息：${NC}"
    echo -e "  Web UI:    http://localhost:${HOST_PORT}"
    echo -e "  API:       http://localhost:${HOST_PORT}/api"
    echo -e "  健康檢查:  http://localhost:${HOST_PORT}/health"
    echo ""
    echo -e "${BLUE}📁 本地掛載目錄：${NC}"
    echo -e "  日誌: ${LOGS_DIR}"
    echo -e "  輸出: ${OUTPUT_DIR}"
    echo ""
    echo -e "${BLUE}常用命令：${NC}"
    echo -e "  查看應用日誌: ${GREEN}./run_docker.sh logs${NC}"
    echo -e "  查看容器日誌: ${GREEN}./run_docker.sh logs docker${NC}"
    echo -e "  進入 Shell: ${GREEN}./run_docker.sh shell${NC}"
    echo -e "  停止並移除服務: ${GREEN}./run_docker.sh down${NC}"
}

# 主函式
main() {
    local command=${1:-up}

    case "$command" in
    up)
        start_container
        ;;
    down)
        remove_container
        ;;
    restart)
        restart_container
        ;;
    pull)
        pull_image
        ;;
    logs)
        show_logs "${2:-app}"
        ;;
    shell)
        enter_shell "${2:-$CONTAINER_NAME}"
        ;;
    clean)
        clean_up
        ;;
    info)
        show_info
        ;;
    help | -h | --help)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $command${NC}"
        echo ""
        echo -e "${BLUE}使用 '${GREEN}./run_docker.sh help${BLUE}' 查看完整幫助信息${NC}"
        echo ""
        echo "快速命令列表:"
        echo "  up      - 啟動服務"
        echo "  down    - 停止並移除服務"
        echo "  restart - 重啟服務"
        echo "  pull    - 拉取鏡像"
        echo "  logs    - 查看應用日誌"
        echo "  shell   - 進入容器"
        echo "  info    - 顯示信息"
        echo "  clean   - 清理資源"
        echo "  help    - 顯示幫助"
        exit 1
        ;;
    esac
}

main "$@"
