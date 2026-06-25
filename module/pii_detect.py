import grpc, os, sys
from google.protobuf.json_format import MessageToDict
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.insert(0, current_dir)

from logger_config import logger
import pii_pb2, pii_pb2_grpc

load_dotenv(dotenv_path=".env")

PII_API_URL = os.environ.get("PII")

def run_pii_detect(target_text, ruleset="default_rules"):
    with grpc.insecure_channel(PII_API_URL) as channel:
        stub = pii_pb2_grpc.PiiDetectorStub(channel)
        request_data = pii_pb2.DetectRequest(text=target_text, max_results_per_type=10, ruleset=ruleset)
        try:
            response = stub.Detect(request_data)
            response_dict = MessageToDict(response, always_print_fields_with_no_presence=True)
            response_dict.pop("meta", None)
            return response_dict
        except grpc.RpcError as e:
            logger.error(f"🚨 gRPC 통신 장애 발생: {e.code()} - {e.details()}")
            return None


def process_dynamic_pii_list(data_list, ruleset="default_rules"):
    processed_item = {
        "body": {},
        "attach": []
    }

    for idx, item in enumerate(data_list):
        for key, text_value in item.items():
            #logger.info(f"{key}")
            detection_result = run_pii_detect(text_value, ruleset=ruleset)
            
            if key == "body":
                processed_item["body"] = detection_result
            else:
                processed_item["attach"].append({key: detection_result})
    return processed_item