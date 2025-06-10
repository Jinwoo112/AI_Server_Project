import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from gtts import gTTS
from app.ai_model import analyze_image  # 이제 이 함수가 여러 모델을 동시에 분석

router = APIRouter()

UPLOAD_DIR = "static/uploads"
TTS_DIR    = "static/tts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

stored_result: dict = {}

@router.post("/analyze_image")
async def analyze_and_tts(request: Request):
    ctype = request.headers.get("content-type", "")
    if not ctype.startswith("application/octet-stream"):
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    img_name = f"{uuid.uuid4().hex}.jpg"
    img_path = os.path.join(UPLOAD_DIR, img_name)
    with open(img_path, "wb") as f:
        f.write(body)

    try:
        result = analyze_image(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

    # TTS 메시지 순서: 점자블럭 → 횡단보도 → 신호등
    tts_lines = []
    if result.get("has_braille"):
        tts_lines.append("점자블럭이 있습니다.")
    if result.get("has_crosswalk"):
        tts_lines.append("횡단보도가 있습니다.")
    if result.get("traffic_label"):
        tts_lines.append(result["traffic_label"])

    tts_message = " ".join(tts_lines) if tts_lines else "감지된 객체가 없습니다."
    tts_name = None

    if tts_lines:
        tts_name = f"{uuid.uuid4().hex}.mp3"
        tts_path = os.path.join(TTS_DIR, tts_name)
        try:
            tts = gTTS(text=tts_message, lang="ko")
            tts.save(tts_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    stored_result['result'] = result
    stored_result['tts'] = tts_name

    response = {'result': result}
    if tts_name:
        response['tts_url'] = '/latest_tts'
    return JSONResponse(response)

@router.get("/latest_detection")
async def latest_detection():
    if 'result' not in stored_result:
        raise HTTPException(status_code=404, detail="No detections yet")
    resp = {'result': stored_result['result']}
    if stored_result.get('tts'):
        resp['tts_url'] = '/latest_tts'
    return JSONResponse(resp)

@router.get("/tts/{filename}")
def serve_tts(filename: str):
    path = os.path.join(TTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="TTS file not found")
    return FileResponse(path, media_type="audio/mpeg")

@router.get("/latest_tts")
def latest_tts():
    tts_file = stored_result.get('tts')
    if not tts_file:
        raise HTTPException(status_code=404, detail="No TTS available yet")
    path = os.path.join(TTS_DIR, tts_file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="TTS file not found")
    return FileResponse(path, media_type="audio/mpeg")
