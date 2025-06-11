import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from gtts import gTTS
from app.ai_model import analyze_image

# FastAPI 라우터 생성 / Create FastAPI router
router = APIRouter()

# 업로드/음성 파일 저장 경로 생성 / Make directories for uploads and TTS
UPLOAD_DIR = "static/uploads"
TTS_DIR    = "static/tts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# 최근 감지 결과를 임시 저장 / Store the latest detection result
stored_result: dict = {}

@router.post("/analyze_image")
async def analyze_and_tts(request: Request):
    # 요청 헤더에서 content-type 확인 / Check content-type in request header
    ctype = request.headers.get("content-type", "")
    if not ctype.startswith("application/octet-stream"):
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    # 이미지 바디 데이터 수신 / Receive image body data
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    # 파일 이름 랜덤 생성 후 저장 / Generate random file name and save image
    img_name = f"{uuid.uuid4().hex}.jpg"
    img_path = os.path.join(UPLOAD_DIR, img_name)
    with open(img_path, "wb") as f:
        f.write(body)

    try:
        # AI 모델로 이미지 분석 / Analyze image with AI model
        result = analyze_image(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

    # 분석 결과 값 분리 / Separate detection results
    traffic_label = result.get("traffic_label", "")
    objects = result.get("objects_on_crosswalk", [])
    has_crosswalk = result.get("has_crosswalk", False)

    tts_lines = []

    # 신호등 메시지 추가 / Add basic traffic light message
    if traffic_label:
        if traffic_label == "초록불":
            tts_lines.append("초록불입니다. 횡단하세요.")
        elif traffic_label == "빨간불":
            tts_lines.append("빨간불입니다. 건너지 마세요.")

    # 조건에 따른 추가 메시지 / Add extra message by situation
    if traffic_label == "초록불" and any(o in ["car", "truck", "bus", "obstacle"] for o in objects):
        tts_lines.append("차량 또는 장애물이 횡단보도를 막고 있습니다. 후진해주세요.")
    elif traffic_label == "빨간불" and "person" in objects:
        tts_lines.append("사람이 횡단보도 위에 있습니다. 건너지 마세요.")

    # 신호등 없는 경우 메시지 / Message if only crosswalk is detected
    if not traffic_label and has_crosswalk:
        tts_lines.append("횡단보도를 감지했습니다.")

    # 최종 TTS 메시지 생성 / Generate final TTS message
    tts_message = " ".join(tts_lines) if tts_lines else "감지된 객체가 없습니다."
    tts_name = None

    # TTS 파일 생성 / Generate TTS mp3 file if needed
    if tts_lines:
        tts_name = f"{uuid.uuid4().hex}.mp3"
        tts_path = os.path.join(TTS_DIR, tts_name)
        try:
            tts = gTTS(text=tts_message, lang="ko")
            tts.save(tts_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    # 결과 및 TTS 파일 이름 저장 / Save result and TTS filename
    stored_result['result'] = result
    stored_result['tts'] = tts_name

    # 클라이언트로 응답 반환 / Return response to client
    response = {'result': result}
    if tts_name:
        response['tts_url'] = '/latest_tts'
    return JSONResponse(response)

@router.get("/latest_detection")
async def latest_detection():
    # 최근 감지 결과 반환 / Return latest detection result
    if 'result' not in stored_result:
        raise HTTPException(status_code=404, detail="No detections yet")
    resp = {'result': stored_result['result']}
    if stored_result.get('tts'):
        resp['tts_url'] = '/latest_tts'
    return JSONResponse(resp)

@router.get("/tts/{filename}")
def serve_tts(filename: str):
    # 요청된 TTS 파일 반환 / Serve requested TTS file
    path = os.path.join(TTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="TTS file not found")
    return FileResponse(path, media_type="audio/mpeg")

@router.get("/latest_tts")
def latest_tts():
    # 가장 최근 TTS 파일 반환 / Serve latest TTS file
    tts_file = stored_result.get('tts')
    if not tts_file:
        raise HTTPException(status_code=404, detail="No TTS available yet")
    path = os.path.join(TTS_DIR, tts_file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="TTS file not found")
    return FileResponse(path, media_type="audio/mpeg")
