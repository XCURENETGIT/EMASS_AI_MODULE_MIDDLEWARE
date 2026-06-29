import json, os, time
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from logger_config import logger
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from module.get_data import get_body_text, get_image_path, get_attach_text
from module.image_classify import image_classify
from module.code_text_detect import process_dynamic_classify_list
from module.pii_detect import process_dynamic_pii_list

load_dotenv()

# 환경변수 바인딩
BOOTSTRAP_SERVERS = os.environ.get("KAFKA_SERVER_URL")
KAFKA_PORT = os.environ.get("KAFKA_PORT")
CONSUMER_GROUP_ID = os.environ.get("KAFKA_GROUP")
CONSUMER_TOPIC_NAME = os.environ.get("KAFKA_SOURCE_TOPIC")
PRODUCER_TOPIC_NAME = os.environ.get("KAFKA_TARGET_TOPIC")
raw_prefixes = os.environ.get("IGNORE_SVC_PREFIXES")
IGNORE_PREFIXES = tuple(p.strip().upper() for p in raw_prefixes.split(",") if p.strip())

# (이하 카프카 설정 및 메인 루프 코드는 동일)
consumer_config = {
    "bootstrap.servers": f"{BOOTSTRAP_SERVERS}:{KAFKA_PORT}",
    "group.id": CONSUMER_GROUP_ID,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
}

producer_config = {
    "bootstrap.servers": f"{BOOTSTRAP_SERVERS}:{KAFKA_PORT}",
    "acks": "all",
    "compression.type": "snappy"
}

# 모듈별 처리 시간 측정용 헬퍼 (반환값은 그대로 전달)
def timed(name, fn, *args, **kwargs):
    t0 = time.perf_counter()
    try:
        return fn(*args, **kwargs)
    finally:
        logger.info(f"[타이밍] {name} 소요: {time.perf_counter() - t0:.3f}초")


# 프로듀서 전송 결과 비동기 콜백 함수
def delivery_report(err, msg):
    if err is not None:
        logger.error(f"프로듀서 메시지 전달 실패: {err}")
    else:
        # 분리된 로그 파일에 프로듀서 전송 성공 팩트 기록
        logger.info(f"프로듀서 전송 완료 ➡️ 토픽: {msg.topic()} [파티션: {msg.partition()}]")



def process_message(msg,executor):
    try:
        if msg.key() is not None:
            msgKey = msg.key().decode("utf-8")
        else:
            logger.info("Received message with no key content")
            msgKey = None

        if msg.value() is not None:
            msgContents = msg.value().decode("utf-8")
            msgJson = json.loads(msgContents)
        else:
            logger.info("Received message with no content")
            return None

        # svc 가 환경설정에 있는 서비스타입이 아닌 경우에만 진행
        svc_value = msgJson.get('svc', '').strip().upper()
        if svc_value and svc_value.startswith(IGNORE_PREFIXES):
            # 처리 대상이 아닌 메시지는 타이밍/로그 없이 조용히 스킵
            return None

        # 여기서부터가 실제 처리 대상 메시지 (타이밍 측정 시작)
        start_time = time.perf_counter()
        try:
            logger.info(f"Processing message key: {msgKey}")
            body = timed("get_body_text", get_body_text, msgKey)
            image_path = timed("get_image_path", get_image_path, msgKey)
            text = timed("get_attach_text", get_attach_text, msgKey)
            #text['body'] = body
            text.append({'body':body})
            future_to_task = {
            executor.submit(timed, "pii", process_dynamic_pii_list, text): "pii",
            executor.submit(timed, "classify", process_dynamic_classify_list, text): "classify",
            executor.submit(timed, "image", image_classify, image_path): "image"
            }

            task_results = {}

            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    data = future.result()  # 개별 스레드 작업 완료 결과물 획득
                    task_results[task_name] = data
                except Exception as exc:
                    logger.error(f"하위 스레드 [{task_name}] 실행 중 예외 터짐: {exc}")
                    task_results[task_name] = None

            processed = {"type" : "normal", "key": msgKey, "data": task_results}
            logger.info(f'최종 결과물 : {processed}')
            return processed

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return None




def main():
    consumer = Consumer(consumer_config)
    producer = Producer(producer_config)
    consumer.subscribe([CONSUMER_TOPIC_NAME])

    # 최대 4개 스레드에서 병렬 처리
    max_workers = 4
    executor = ThreadPoolExecutor(max_workers=max_workers)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    break
            else:
                # 메시지 처리를 스레드 풀에 위임
                future = executor.submit(process_message, msg, executor)
                try:
                    result = future.result(timeout=30)
                    if result is not None:
                        # 결과 메시지 생성
                        result_json = json.dumps(result, ensure_ascii=False)
                        producer.produce(
                            PRODUCER_TOPIC_NAME,
                            key=msg.key(),
                            value=result_json.encode("utf-8"),
                            callback=delivery_report
                        )
                        producer.poll(0)
                except Exception as e:
                    logger.error(f"Message processing failed: {e}")
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        consumer.close()
        executor.shutdown(wait=True)

if __name__ == "__main__":
    main()
