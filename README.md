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
| `manage.sh` | 서비스 관리 스크립트 (start, stop, restart, status, logs, clean_logs, health_check) |
| `manage-guide.md` | 관리 가이드 문서 |
| `config/.env` | 환경 변수 설정 파일 |

## 📖 관리 가이드

### manage.sh 사용법

`manage.sh` 스크립트를 사용하여 서비스를 간편하게 관리할 수 있습니다.

```bash
# 서비스 시작
./manage.sh start

# 서비스 중지
./manage.sh stop

# 서비스 재시작
./manage.sh restart

# 서비스 상태 확인
./manage.sh status

# 로그 확인
./manage.sh logs

# 로그 정리
./manage.sh clean_logs

# 헬스 체크
./manage.sh health_check
```

### 환경 변수 설정

`config/.env` 파일을 사용하여 환경 변수를 설정합니다.

```bash
# 환경 변수 파일 복사
cp config/.env workspace/.env

# 또는 직접 편집
vi workspace/.env
```

#### 주요 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `KAFKA_SERVER_URL` | Kafka 서버 주소 | `10.200.10.64` |
| `KAFKA_PORT` | Kafka 포트 | `9092` |
| `KAFKA_GROUP` | Kafka 컨슈머 그룹 | `ai_grp` |
| `KAFKA_SOURCE_TOPIC` | 소스 토픽 | `analysis` |
| `KAFKA_TARGET_TOPIC` | 대상 토픽 | `analysis_result` |
| `MONGODB_SERVER_URL` | MongoDB 서버 주소 | `10.200.10.65` |
| `MONGO_PORT` | MongoDB 포트 | `27018` |
| `DATABASE_NAME` | 데이터베이스 이름 | `venus` |
| `MINIO_PORT` | MinIO 포트 | `19000` |
| `MINIO_BUCKET` | MinIO 버킷 | `emass` |
| `ACCESS_KEY` | MinIO 접근 키 | `minioadmin` |
| `SECRET_KEY` | MinIO 시크릿 키 | `minioadmin` |
| `LOG_DIR_PATH` | 로그 디렉토리 | `/app/ai_process_log` |
| `PII` | PII API 주소 | `10.200.10.222:50055` |
| `CLASSIFY` | 문서 분류 API | `http://10.200.10.222:15000/api/data-analyze` |
| `IMAGE` | 이미지 분류 API | `http://10.100.40.51:8000/detect/batch` |

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

### 2. Docker 실행

```bash
docker-compose up --build
```
