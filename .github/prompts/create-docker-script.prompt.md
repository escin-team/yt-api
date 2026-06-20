---
mode: agent
description: "Create scripts to build and run Docker containers for the project."
---

# 建立 Docker 腳本步驟

## 1. 在專案根目錄 (${workspaceFolder}) 下建立 scripts 目錄（如果尚未存在）

```bash
mkdir -p ${workspaceFolder}/scripts
```

## 2. 在 scripts 目錄下建立 Dockerfile

- Dockerfile: 分析專案需求，建立適合的 Dockerfile 來構建映像檔。
- 將 .env 檔案複製到 scripts 目錄改名為 .env.docker 作為容器環境變數配置範例。

## 3. 詢問使用者輸入必要的環境變數

- `DOCKER_USERNAME`: Docker Hub 使用者名稱 (選填)
- `DOCKER_IMAGE_NAME`: 映像檔名稱 (必填)
- `DOCKER_TAG`: 映像檔標籤 (選填，預設: latest)
- `CONTAINER_NAME`: 執行容器名稱 (選填，預設: 與映像檔名稱相同)
- `HOST_PORT`: 映射到主機的埠號 (選填，預設: 8000)

## 4. 在 scripts 目錄下建立 build_docker.sh 腳本，內容如下

```bash
#!/bin/zsh
# ============================================
# Build and Deploy Script for YTSearch
# ============================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${ZSH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Configuration
DOCKER_IMAGE_NAME="{{ 映像檔名稱 }}"
DOCKER_TAG="{{ 映像檔標籤 }}"
DOCKER_USERNAME="{{ Docker Hub 使用者名稱 }}"

# Function to display usage
show_usage() {
    echo "Usage: ./build_docker.sh [OPTIONS]"
    echo ""
    echo "Options (interactive if not provided):"
    echo "  --platform PLATFORM    Select platform: arm64, amd64, or all"
    echo "  --action ACTION        Select action: build, push, or build-push"
    echo "  --no-interactive       Use defaults without prompting"
    echo "  --help                 Show this help message"
    echo ""
    echo "Environment Variables (Required):"
    echo "  DOCKER_USERNAME        Docker Hub username"
    echo "  DOCKER_IMAGE_NAME      Image name"
    echo "  DOCKER_TAG             Image tag"
}

# Parse command line arguments
PLATFORM=""
ACTION=""
INTERACTIVE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --no-interactive)
            INTERACTIVE=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check and prompt for required environment variables
if [ -z "$DOCKER_USERNAME" ]; then
    echo ""
    echo "================================================"
    echo "Docker Configuration"
    echo "================================================"
    echo -n "Enter Docker Hub username: "
    read DOCKER_USERNAME
    if [ -z "$DOCKER_USERNAME" ]; then
        echo "❌ Error: Docker Hub username is required"
        exit 1
    fi
fi

if [ -z "$DOCKER_IMAGE_NAME" ]; then
    echo -n "Enter Docker image name [noname]: "
    read DOCKER_IMAGE_NAME
    DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME:-noname}
fi

if [ -z "$DOCKER_TAG" ]; then
    echo -n "Enter Docker image tag [latest]: "
    read DOCKER_TAG
    DOCKER_TAG=${DOCKER_TAG:-latest}
fi

# Interactive selection for platform
if [ -z "$PLATFORM" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "================================================"
    echo "Platform Selection"
    echo "================================================"
    echo "1. arm64 (M1/M2/M3 Mac, ARM servers)"
    echo "2. amd64 (Intel Mac, x86_64 servers)"
    echo "3. all (arm64 + amd64)"
    echo ""
    echo -n "Select platform (1-3) [default: 1]: "
    read platform_choice
    platform_choice=${platform_choice:-1}

    case $platform_choice in
        1) PLATFORM="arm64" ;;
        2) PLATFORM="amd64" ;;
        3) PLATFORM="all" ;;
        *)
            echo "❌ Invalid choice. Using default: arm64"
            PLATFORM="arm64"
            ;;
    esac
elif [ -z "$PLATFORM" ]; then
    PLATFORM="arm64"
fi

# Validate platform choice
case $PLATFORM in
    arm64) PLATFORMS="linux/arm64" ;;
    amd64) PLATFORMS="linux/amd64" ;;
    all)   PLATFORMS="linux/arm64,linux/amd64" ;;
    *)
        echo "❌ Invalid platform: $PLATFORM"
        echo "Valid options: arm64, amd64, all"
        exit 1
        ;;
esac

# Interactive selection for action
if [ -z "$ACTION" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "================================================"
    echo "Action Selection"
    echo "================================================"
    echo "1. build (only build, no push)"
    echo "2. push (only push existing image)"
    echo "3. build-push (build then push) [default]"
    echo ""
    echo -n "Select action (1-3) [default: 3]: "
    read action_choice
    action_choice=${action_choice:-3}

    case $action_choice in
        1) ACTION="build" ;;
        2) ACTION="push" ;;
        3) ACTION="build-push" ;;
        *)
            echo "❌ Invalid choice. Using default: build-push"
            ACTION="build-push"
            ;;
    esac
elif [ -z "$ACTION" ]; then
    ACTION="build-push"
fi

# Validate action choice
case $ACTION in
    build|push|build-push) ;;
    *)
        echo "❌ Invalid action: $ACTION"
        echo "Valid options: build, push, build-push"
        exit 1
        ;;
esac

# Full image name
FULL_IMAGE_NAME="$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:$DOCKER_TAG"

echo ""
echo "================================================"
echo "YTSearch - Build and Deploy"
echo "================================================"
echo "Image: $FULL_IMAGE_NAME"
echo "Platforms: $PLATFORMS"
echo "Action: $ACTION"
echo "================================================"

# Step 0: Setup Docker buildx for multi-platform builds (required for Mac to build Linux images)
echo ""
echo "⚙️  Step 0: Setting up Docker buildx for multi-platform builds..."
echo "================================================"

BUILDER_NAME="multiarch-builder"

if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    echo "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
    echo "Using existing buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

docker buildx inspect --bootstrap

echo "Registering QEMU multiarch binfmt support (requires Docker privileged mode)..."
docker run --rm --privileged tonistiigi/binfmt:latest --install all || \
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true

echo "✅ Docker buildx setup complete!"

# Step 1: Build Docker Image (if action is build or build-push)
if [ "$ACTION" != "push" ]; then
    echo ""
    echo "🏗️  Step 1: Building Docker image for platforms: $PLATFORMS"
    echo "================================================"

    cd "$PROJECT_ROOT"

    # Determine push flag based on action
    PUSH_FLAG="--load"
    if [ "$ACTION" = "build-push" ]; then
        PUSH_FLAG="--push"
    fi

    docker buildx build \
        --platform "$PLATFORMS" \
        $PUSH_FLAG \
        -t "$FULL_IMAGE_NAME" \
        -f "$SCRIPT_DIR/Dockerfile" \
        "$PROJECT_ROOT"

    echo "✅ Docker image built successfully!"
else
    echo ""
    echo "⏭️  Skipping build step (push-only action)"
fi

# Step 2: Push Docker Image (if action is push or build-push)
if [ "$ACTION" != "build" ]; then
    echo ""
    echo "📤 Step 2: Pushing Docker image to registry"
    echo "================================================"

    docker buildx build \
        --platform "$PLATFORMS" \
        --push \
        -t "$FULL_IMAGE_NAME" \
        -f "$SCRIPT_DIR/Dockerfile" \
        "$PROJECT_ROOT"

    echo "✅ Docker image pushed successfully!"
else
    echo ""
    echo "⏭️  Skipping push step (build-only action)"
fi

echo ""
echo "================================================"
echo "🎉 All done!"
echo "================================================"
echo "Image: $FULL_IMAGE_NAME"
echo "Platforms: $PLATFORMS"
echo ""
```

## 5. 在 scripts 目錄下建立 run_docker.sh 腳本，內容如下

```bash
#!/bin/bash

# 用法：./docker-run.sh [command] [options]
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
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 預設環境文件
ENV_FILE="${SCRIPT_DIR}/.env.docker"

# Docker 鏡像和容器名稱
IMAGE_NAME="{{ Docker Hub 使用者名稱 }}/${{ 映像檔名稱 }}:{{ Docker 標籤 }}"
CONTAINER_NAME="{{ 執行容器名稱 }}"
HOST_PORT="{{ 映射到主機的埠號 }}"

# Docker 網路名稱
NETWORK_NAME="sacahan-network"

# 日誌和輸出目錄
LOGS_DIR="${SCRIPT_DIR}/logs"
OUTPUT_DIR="${SCRIPT_DIR}/output"

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

# 確保 Docker 網路存在
ensure_network() {
 if ! docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
  echo -e "${BLUE}📡 建立 Docker 網路: $NETWORK_NAME${NC}"
  docker network create "$NETWORK_NAME"
  echo -e "${GREEN}✓ Docker 網路已建立${NC}"
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
  echo -e "   使用 ${GREEN}./docker-run.sh up${NC} 啟動容器"
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
 local container=$1

 if [ -z "$container" ]; then
  container="$CONTAINER_NAME"
 fi

 echo -e "${BLUE}📋 顯示 $container 容器日誌（按 Ctrl+C 退出）...${NC}"
 docker logs -f "$container"
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
 cat << 'EOF'
MediaGrabber Docker 執行腳本

用法: ./docker-run.sh [command]

📋 命令:

  up         啟動容器
  down       停止並移除容器
  restart    重啟容器
  pull       拉取鏡像
  logs       查看日誌
  shell      進入容器 shell
  info       服務信息
  clean      清理資源
  help       顯示此幫助信息

🚀 快速開始:

  1. 拉取鏡像:
     ./docker-run.sh pull

  2. 啟動服務:
     ./docker-run.sh up

  3. 查看日誌:
     ./docker-run.sh logs

  4. 停止並移除服務:
     ./docker-run.sh down

🔗 服務端點:
  Web UI:    http://localhost:8000
  API:       http://localhost:8000/api
  健康檢查:  http://localhost:8000/health

📝 環境配置:
  配置文件: .env.docker
  日誌目錄: logs/
  輸出目錄: output/

💡 更多幫助: ./docker-run.sh info

EOF
}

# 顯示服務信息
show_info() {
 echo -e "${BLUE}📊 MediaGrabber 服務信息：${NC}"
 echo -e "  Web UI:    http://localhost:${HOST_PORT}"
 echo -e "  API:       http://localhost:${HOST_PORT}/api"
 echo -e "  健康檢查:  http://localhost:${HOST_PORT}/health"
 echo ""
 echo -e "${BLUE}📁 本地掛載目錄：${NC}"
 echo -e "  日誌: ${LOGS_DIR}"
 echo -e "  輸出: ${OUTPUT_DIR}"
 echo ""
 echo -e "${BLUE}常用命令：${NC}"
 echo -e "  查看日誌: ${GREEN}./docker-run.sh logs${NC}"
 echo -e "  進入 Shell: ${GREEN}./docker-run.sh shell${NC}"
 echo -e "  停止並移除服務: ${GREEN}./docker-run.sh down${NC}"
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
  show_logs "${2:-$CONTAINER_NAME}"
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
 help|-h|--help)
  show_help
  ;;
 *)
  echo -e "${RED}❌ 未知命令: $command${NC}"
  echo ""
  echo -e "${BLUE}使用 '${GREEN}./docker-run.sh help${BLUE}' 查看完整幫助信息${NC}"
  echo ""
  echo "快速命令列表:"
  echo "  up      - 啟動服務"
  echo "  down    - 停止並移除服務"
  echo "  restart - 重啟服務"
  echo "  pull    - 拉取鏡像"
  echo "  logs    - 查看日誌"
  echo "  shell   - 進入容器"
  echo "  info    - 顯示信息"
  echo "  clean   - 清理資源"
  echo "  help    - 顯示幫助"
  exit 1
  ;;
 esac
}

main "$@"

```

### 6. 設定腳本執行權限

```bash
chmod +x ${workspaceFolder}/scripts/build_docker.sh
chmod +x ${workspaceFolder}/scripts/run_docker.sh
```

Let's do it step by step!
