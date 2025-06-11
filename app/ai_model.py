from ultralytics import YOLO
import cv2
import numpy as np

# ✅ YOLOv8 모델 경로 설정 / Set YOLOv8 model paths
MODEL_PATHS = {
    "braille": "../models/braille.pt",
    "crosswalk": "../models/crosswalk.pt",
    "traffic": "../models/traffic.pt",
}
models = {k: YOLO(v) for k, v in MODEL_PATHS.items()}  # 각 모델 불러오기 / Load each YOLO model

# 🔄 B↔R 채널 스왑 함수 / Swap Blue and Red channels in image
# ESP32-CAM의 빨간색이 파란색으로 보이는 이슈때문에 추가했습니다.
def swap_blue_red_channel(img_bgr):
    return img_bgr[:, :, ::-1].copy()

# ✅ 이미지 분석 함수 / Main image analysis function
def analyze_image(image_path):
    img = cv2.imread(image_path)  # 이미지 읽기 / Read image file

    # 🔄 색상 반전 대신 B↔R 채널 교환 / Swap B and R channels instead of invert
    img = swap_blue_red_channel(img)

    # YOLO 입력용 RGB 변환 / Convert image to RGB for YOLO input
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 🔍 YOLO로 횡단보도/신호등 추론 / Run YOLO inference (crosswalk, traffic)
    crosswalk_result = models["crosswalk"](img_rgb)
    traffic_result = models["traffic"](img_rgb)

    # 예측 결과 이미지 저장(디버깅용) / Save inference result for debugging
    traffic_result[0].save("output.jpg")

    # 횡단보도 박스 감지 / Detect crosswalk boxes
    boxes = crosswalk_result[0].boxes
    has_crosswalk = len(boxes) > 0

    crosswalk_area = None
    if has_crosswalk:
        # 가장 큰 박스 선택 / Select biggest crosswalk box
        biggest_box = max(
            boxes,
            key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1])
        )
        crosswalk_area = biggest_box.xyxy[0].cpu().numpy()

    # 신호등 예측 결과에서 클래스명 추출 / Extract class names from traffic results
    traffic_classes = [
        traffic_result[0].names[int(c)].lower()
        for c in traffic_result[0].boxes.cls.cpu().numpy()
    ]
    print("🔥 감지된 클래스:", traffic_classes)

    # 신호등 상태 판단 / Judge traffic light state
    has_red = any("traffic light-red-" in cls for cls in traffic_classes)
    has_green = any("traffic light-green-" in cls for cls in traffic_classes)

    if has_red and has_green:
        traffic_label = "⚠️ 빨간불과 초록불이 동시에 감지됨"  # 둘 다 감지 시 / Both detected
    elif has_red:
        traffic_label = "빨간불"  # 빨간불 감지 / Red detected
    elif has_green:
        traffic_label = "초록불"  # 초록불 감지 / Green detected
    else:
        traffic_label = ""  # 감지된 신호등 없음 / No light detected

    print("🚦 판단된 신호등 상태:", traffic_label)

    # 횡단보도 위 객체 탐지 / Detect objects on crosswalk
    objects_on_crosswalk = []
    if crosswalk_area is not None:
        x1, y1, x2, y2 = crosswalk_area
        for box in traffic_result[0].boxes:
            cls = traffic_result[0].names[int(box.cls[0])].lower()
            if cls in ["person", "car", "truck", "bus"]:
                bx1, by1, bx2, by2 = box.xyxy[0].cpu().numpy()
                cx, cy = (bx1 + bx2) / 2, (by1 + by2) / 2
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    objects_on_crosswalk.append(cls)  # 중심점이 횡단보도 내부면 추가 / Add if center in crosswalk

    # 분석 결과 딕셔너리로 반환 / Return results as dictionary
    return {
        "has_crosswalk": has_crosswalk,
        "traffic_label": traffic_label,
        "objects_on_crosswalk": objects_on_crosswalk
    }
