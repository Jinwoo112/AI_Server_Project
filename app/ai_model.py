from ultralytics import YOLO
import cv2

# ✅ YOLOv8 모델 로드 (자동으로 GPU 사용)
model = YOLO('models/model.pt')

def analyze_image(image_array):
    # YOLOv8 추론 실행
    results = model(image_array)

    # 결과 요약: 클래스명 + 신뢰도 추출
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            detections.append({
                "class": model.names[cls_id],
                "confidence": round(conf, 3)
            })
    
    return {"detections": detections}
