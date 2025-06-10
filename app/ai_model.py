from ultralytics import YOLO
import cv2
from PIL import Image
import numpy as np

# ✅ 3개 YOLOv8 모델 로딩
MODEL_PATHS = {
    "braille": "..../braille.pt",
    "crosswalk": "..../crosswalk.pt",
    "traffic": "..../traffic.pt",
}
models = {k: YOLO(v) for k, v in MODEL_PATHS.items()}

def analyze_image(image_path):
    # 이미지 로드 (cv2 or PIL 둘 다 가능)
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = {}

    # 1) 점자블럭 모델 추론
    braille_result = models["braille"](img_rgb)
    has_braille = len(braille_result[0].boxes) > 0

    # 2) 횡단보도 모델 추론
    crosswalk_result = models["crosswalk"](img_rgb)
    has_crosswalk = len(crosswalk_result[0].boxes) > 0

    # 3) 신호등 모델 추론
    traffic_result = models["traffic"](img_rgb)
    traffic_label = ""
    if len(traffic_result[0].boxes) > 0:
        class_ids = traffic_result[0].boxes.cls.cpu().numpy().astype(int)
        class_names = [traffic_result[0].names[i] for i in class_ids]
        # 신호등 라벨명이 실제로 '빨간불', '녹색불'인지 체크
        if "빨간불" in class_names:
            traffic_label = "빨간불입니다."
        elif "녹색불" in class_names:
            traffic_label = "녹색불입니다."

    # 감지 결과를 딕셔너리로 반환
    return {
        "has_braille": has_braille,
        "has_crosswalk": has_crosswalk,
        "traffic_label": traffic_label,
        "detections": {  # 참고용, 필요 없으면 삭제해도 됨
            "braille": [models["braille"].names[int(b.cls[0])] for r in braille_result for b in r.boxes] if has_braille else [],
            "crosswalk": [models["crosswalk"].names[int(b.cls[0])] for r in crosswalk_result for b in r.boxes] if has_crosswalk else [],
            "traffic": [traffic_result[0].names[int(b.cls[0])] for b in traffic_result[0].boxes] if traffic_label else [],
        }
    }
