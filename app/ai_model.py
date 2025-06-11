from ultralytics import YOLO
import cv2
import numpy as np

# ✅ YOLOv8 모델 경로 설정
MODEL_PATHS = {
    "braille": "../models/braille.pt",
    "crosswalk": "../models/crosswalk.pt",
    "traffic": "../models/traffic.pt",
}
models = {k: YOLO(v) for k, v in MODEL_PATHS.items()}  # 모델 로드 방식 원래대로 유지

# 🔄 B↔R 채널 스왑 함수
def swap_blue_red_channel(img_bgr):
    return img_bgr[:, :, ::-1].copy()

# ✅ 이미지 분석 함수
def analyze_image(image_path):
    img = cv2.imread(image_path)

    # 🔄 색상 반전 대신 B↔R 채널 교환만 수행
    img = swap_blue_red_channel(img)

    # RGB로 변환 (YOLO 입력용)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 🔍 YOLO 예측
    crosswalk_result = models["crosswalk"](img_rgb)
    traffic_result   = models["traffic"](img_rgb)

    # 예측 시각화 저장
    traffic_result[0].save("output.jpg")

    # 횡단보도 영역 추출 (가장 큰 박스)
    crosswalk_area = None
    if crosswalk_result[0].boxes:
        biggest_box = max(
            crosswalk_result[0].boxes,
            key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1])
        )
        crosswalk_area = biggest_box.xyxy[0].cpu().numpy()

    # 감지된 클래스명 추출
    traffic_classes = [
        traffic_result[0].names[int(c)].lower()
        for c in traffic_result[0].boxes.cls.cpu().numpy()
    ]
    print("🔥 감지된 클래스:", traffic_classes)

    # 신호등 판단
    has_red = any("traffic light-red-" in cls for cls in traffic_classes)
    has_green = any("traffic light-green-" in cls for cls in traffic_classes)
    if has_red and has_green:
        traffic_label = "⚠️ 빨간불과 초록불이 동시에 감지됨"
    elif has_red:
        traffic_label = "빨간불"
    elif has_green:
        traffic_label = "초록불"
    else:
        traffic_label = ""

    print("🚦 판단된 신호등 상태:", traffic_label)

    # 횡단보도 위 객체 탐지
    objects_on_crosswalk = []
    if crosswalk_area is not None:
        x1, y1, x2, y2 = crosswalk_area
        for box in traffic_result[0].boxes:
            cls = traffic_result[0].names[int(box.cls[0])].lower()
            if cls in ["person", "car", "truck", "bus"]:
                bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                cx, cy = (bx1 + bx2) / 2, (by1 + by2) / 2
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    objects_on_crosswalk.append(cls)

    return {
        "has_crosswalk": crosswalk_area is not None,
        "traffic_label": traffic_label,
        "objects_on_crosswalk": objects_on_crosswalk
    }
