import requests,os,sys
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from logger_config import logger

load_dotenv(dotenv_path=".env")

IMG_API_URL = os.environ.get("IMAGE")

def image_classify(items):
    url = IMG_API_URL
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if items == []:
        logger.info("이미지가 존재하지않음")
        return None
    else:
        payload = {"items": items}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"이미지 분류 HTTP 에러 발생: {http_err}")
            if response.text:
                logger.error(f"이미지 분류 에러 상세 내용: {response.text}")
        except Exception as err:
            logger.error(f"이미지 분류 기타 에러 발생: {err}")
        return None