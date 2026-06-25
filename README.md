# EMASS AI Module Middleware

EMASS AI 기반 메시지 분석 파이프라인 미들웨어 — Kafka 컨슈머로 메시지를 소비하여 PII 탐지, 문서 분류, 이미지 분류를 수행하고 결과를 다시 발행하는 Python 서비스입니다.

## 📋 프로젝트 개요

이 프로젝트는 EMASS 시스템에서 수신된 메시지(이메일 등)를 실시간으로 분석하는 AI 파이프라인 미들웨어입니다. Kafka 토픽에서 메시지를 읽어와 여러 AI 분석 모듈을 통해 처리한 후, 분석 결과를 다른 토픽에 발행합니다.

### 주요 기능
- **PII(개인정보) 탐지** — gRPC 기반 개인정보 탐지 API 호출
- **문서 분류** — 생성형 AI 기반 문서/코드 분류
- **이미지 분류** — sigLIP 기반 이미지 카테고리화
- **MongoDB 연동** — GridFS 기반 본문 및 첨부파일 조회
- **MinIO 연동** — 첨부 파일 텍스트 추출

## 🏗️ 아키텍처

```
Kafka (analysis)
    │
    ▼
┌─────────────────────────────┐
│  kafka_worker.py (Main)     │
│  - Consumer / Producer      │
│  - ThreadPoolExecutor       │
└──────────┬──────────────────┘
           │
    ┌──────┼──────────┬──────────┐
    ▼      ▼          ▼          ▼
 get_data  pii_detect  classify  image
 (MongoDB) (gRPC)     (REST)    (REST)
    │      │           │         │
    ▼      ▼           ▼         ▼
  MinIO   PII API   CLASSIFY   IMG API
```

## 📁 파일 구조

| 파일 | 설명 |
|------|------|
| `workspace/kafka_worker.py` | 메인 워커 — Kafka 컨슈머/프로듀서, 비동기 병렬 처리 |
| `workspace/logger_config.py` | 로그 설정 — TimedRotatingFileHandler, 일별 로그 분할 |
| `module/get_data.py` | MongoDB/MinIO 연동 — 본문 추출, 첨부파일 처리 |
| `module/pii_detect.py` | gRPC 기반 개인정보 탐지 |
| `module/code_text_detect.py` | 문서 분류 및 코드 탐지 (REST API) |
| `module/image_classify.py` | 이미지 분류 (REST API) |
| `module/set_minio.py` | MinIO 클라이언트 및 첨부 텍스트 추출 |
| `module/pii.proto` | gRPC 프로토콜 정의 |
| `module/pii_pb2*.py` | gRPC 자동 생성 코드 |
| `Dockerfile` | 컨테이너 빌드 설정 (Python 3.11-slim) |
| `docker-compose.yaml` | 서비스 구성 |
| `requirements.txt` | Python 의존성 |
| `work.sh` | 보안 설정 자동화 스크립트 (auditd, SELinux, Docker daemon) |

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 의존성**:
- `confluent-kafka` — Kafka 클라이언트
- `pymongo` — MongoDB 연결
- `grpcio`, `protobuf` — gRPC 통신
- `minio` — S3 호환 스토리지
- `beautifulsoup4` — HTML 파싱
- `python-dotenv` — 환경변수 로드
- `requests` — HTTP 클라이언트

### 2. 환경변수 설정

`.env` 파일을 작성하거나 시스템 환경변수를 설정합니다:

```bash
export KAFKA_SERVER_URL="10.200.10.64"
export KAFKA_PORT="9092"
export KAFKA_GROUP="ai_grp"
export KAFKA_SOURCE_TOPIC="analysis"
export KAFKA_TARGET_TOPIC="analysis_result"
export MONGODB_SERVER_URL="10.200.10.65"
export MONGO_PORT="27018"
export DATABASE_NAME="venus"
export MINIO_PORT="19000"
export MINIO_BUCKET="emass"
export ACCESS_KEY="minioadmin"
export SECRET_KEY="minioadmin"
export LOG_DIR_PATH="/app/ai_process_log"
export IGNORE_SVC_PREFIXES="U,X"
export PII="10.200.10.222:50055"
export CLASSIFY="http://10.200.10.222:15000/api/data-analyze"
export IMAGE="http://10.100.40.51:8000/detect/batch"
```

### 3. Docker 실행

```bash
docker-compose up --build
```