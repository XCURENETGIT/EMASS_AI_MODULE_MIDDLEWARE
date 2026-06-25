import requests, base64, os, sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from logger_config import logger

load_dotenv(dotenv_path=".env")

DETECT_API_URL = os.environ.get("CLASSIFY")

def encode_text_to_base64(text: str) -> str:
    if not text:
        return ""
    text_bytes = text.encode("utf-8")
    base64_bytes = base64.b64encode(text_bytes)
    return base64_bytes.decode("utf-8")

def text_classify_code_detect(encoded_text: str):
    url = DETECT_API_URL
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"text": encoded_text}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        api_result = response.json()

        custom_response = {
            "success": True,
            "message": "OK",
            "status": "200",  # result 키를 status로 변경하고 값은 "OK"
            "data": {
                "code_exist": api_result.get("code_exist"),
                "keywords": api_result.get("keywords"),
                "probs": api_result.get("probs"),
                "class": api_result.get("class")
            }
        }
        return custom_response

    except requests.exceptions.HTTPError as http_err:   
        logger.error(f"문서분류 및 코드탐지 HTTP 에러 발생: {http_err}")
        if 'response' in locals() and response.text:
            logger.error(f"문서분류 및 코드탐지 에러 상세 내용: {response.text}")
        return {"success": False, "error": f"HTTP Error: {http_err}"}
    except Exception as err:
        logger.error(f"문서분류 및 코드탐지 기타 에러 발생: {err}")
        return {"success": False, "error": str(err)}

def process_dynamic_classify_list(data_list: list) -> dict:
    processed_item = {
        "body": {},
        "attach": []
    }

    for idx, item in enumerate(data_list):
        for key, text_value in item.items():
            logger.info(f"Classify processing key: {key}")
            encoded_text = encode_text_to_base64(text_value)
            detection_result = text_classify_code_detect(encoded_text)
            
            if key == "body":
                processed_item["body"] = detection_result
            else:
                processed_item["attach"].append({key: detection_result})
    return processed_item