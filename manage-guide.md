# EMASS AI Module Middleware - 관리 가이드

## 개요

EMASS AI Module Middleware는 Kafka 컨슈머로 메시지를 소비하여 PII 탐지, 문서 분류, 이미지 분류를 수행하고 결과를 다시 발행하는 Python 서비스입니다. 본 가이드는 서비스 관리에 필요한 모든 정보를 담고 있습니다.

## 서비스 구조

```
┌─────────────────────────────────────────────────────────┐
│                    EMASS AI Module Middleware             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              kafka_worker.py (Main)              │   │
│  │  - Kafka Consumer / Producer                    │   │
│  │  - ThreadPoolExecutor (병렬 처리)                │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         ▼               ▼               ▼               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ get_data │  │ pii_detect│  │ classify │              │
│  │ (MongoDB)│  │ (gRPC)   │  │ (REST)   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│         │               │               │               │
│         ▼               ▼               ▼               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ MinIO    │  │ PII API  │  │ CLASSIFY │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 구성 요소

| 구성 요소 | 설명 |
|-----------|------|
| `kafka_worker.py` | 메인 워커 — Kafka 컨슈머/프로듀서, 비동기 병렬 처리 |
| `logger_config.py` | 로그 설정 — TimedRotatingFileHandler, 일별 로그 분할 |
| `get_data.py` | MongoDB/MinIO 연동 — 본문 추출, 첨부파일 처리 |
| `pii_detect.py` | gRPC 기반 개인정보 탐지 |
| `code_text_detect.py` | 문서 분류 및 코드 탐지 (REST API) |
| `image_classify.py` | 이미지 분류 (REST API) |
| `set_minio.py` | MinIO 클라이언트 및 첨부 텍스트 추출 |

## 관리 가이드

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

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp config/.env workspace/.env
```

### 3. Docker 실행

```bash
docker-compose up --build
```

## 기술 스택

- **Python 3.11** — 메인 언어
- **Kafka (confluent-kafka)** — 메시지 큐
- **MongoDB (pymongo)** — 데이터 저장소
- **gRPC** — PII 탐지 통신
- **MinIO** — 첨부 파일 저장소
- **Docker** — 컨테이너화

## 개발자 정보

- **저장소**: XCURENETGIT/EMASS_AI_MODULE_MIDDELWARE
- **주요 모듈**: PII 탐지, 문서 분류, 이미지 분류
- **로그 디렉토리**: `/app/ai_process_log`
