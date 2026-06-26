#!/bin/bash

# EMASS AI Module Middleware - 관리 스크립트
# 사용법: ./manage.sh {start|stop|restart|status|logs|clean_logs|health_check}

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${SCRIPT_DIR}/workspace"
CONFIG_DIR="${SCRIPT_DIR}/config"
LOG_DIR="${SCRIPT_DIR}/logs"
ENV_FILE="${WORKSPACE_DIR}/.env"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경 변수 로드
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi
}

# 서비스 시작
start_service() {
    echo -e "${BLUE}[INFO]${NC} 서비스 시작 중..."
    load_env
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE" up -d
    echo -e "${GREEN}[SUCCESS]${NC} 서비스 시작 완료"
}

# 서비스 중지
stop_service() {
    echo -e "${BLUE}[INFO]${NC} 서비스 중지 중..."
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}[SUCCESS]${NC} 서비스 중지 완료"
}

# 서비스 재시작
restart_service() {
    echo -e "${BLUE}[INFO]${NC} 서비스 재시작 중..."
    stop_service
    sleep 2
    start_service
}

# 서비스 상태 확인
check_status() {
    echo -e "${BLUE}[INFO]${NC} 서비스 상태 확인 중..."
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
}

# 로그 확인
show_logs() {
    echo -e "${BLUE}[INFO]${NC} 로그 확인 중..."
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
}

# 로그 정리
clean_logs() {
    echo -e "${BLUE}[INFO]${NC} 로그 정리 중..."
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"/*
        echo -e "${GREEN}[SUCCESS]${NC} 로그 정리 완료"
    else
        echo -e "${YELLOW}[WARN]${NC} 로그 디렉토리가 없습니다: $LOG_DIR"
    fi
}

# 헬스 체크
health_check() {
    echo -e "${BLUE}[INFO]${NC} 헬스 체크 중..."
    cd "$SCRIPT_DIR"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo -e "${BLUE}[INFO]${NC} 컨테이너 응답 확인..."
    docker-compose -f "$COMPOSE_FILE" exec middleware python -c "print('Service is running')" 2>/dev/null && echo -e "${GREEN}[SUCCESS]${NC} 서비스 정상" || echo -e "${RED}[FAIL]${NC} 서비스 응답 없음"
}

# 사용법 표시
usage() {
    echo "사용법: $0 {start|stop|restart|status|logs|clean_logs|health_check}"
    echo ""
    echo "명령어:"
    echo "  start        - 서비스 시작"
    echo "  stop         - 서비스 중지"
    echo "  restart      - 서비스 재시작"
    echo "  status       - 서비스 상태 확인"
    echo "  logs         - 로그 확인"
    echo "  clean_logs   - 로그 정리"
    echo "  health_check - 헬스 체크"
}

# 메인
case "${1}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    clean_logs)
        clean_logs
        ;;
    health_check)
        health_check
        ;;
    *)
        usage
        exit 1
        ;;
esac
