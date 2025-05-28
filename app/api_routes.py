import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from gtts import gTTS
from app.ai_model import analyze_image  # AI 모델 분석 함수

router = APIRouter()

# 업로드 및 TTS 저장 디렉터리
UPLOAD_DIR = "static/uploads"
TTS_DIR    = "static/tts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# 최근 결과 및 TTS 파일명 저장용 전역 변수
stored_result: dict = {}

@router.post("/analyze_image")
async def analyze_and_tts(request: Request):
    # 1) Content-Type 검사 (완화)
    ctype = request.headers.get("content-type", "")
    if not ctype.startswith("application/octet-stream"):
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    # 2) 바디(raw bytes) 읽기
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    # 3) 이미지 임시 저장
    img_name = f"{uuid.uuid4().hex}.jpg"
    img_path = os.path.join(UPLOAD_DIR, img_name)
    with open(img_path, "wb") as f:
        f.write(body)

    # 4) AI 모델 분석
    try:
        raw = analyze_image(img_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {e}")

    # 5) result 구조 추출
    result = raw
    if isinstance(raw, dict) and 'result' in raw:
        result = raw['result']

    # 6) detections 리스트 확보
    detections = []
    if isinstance(result, dict) and 'detections' in result:
        detections = result['detections'] or []
    elif isinstance(result, list):
        detections = result

    # 7) TTS 생성 조건: detections 안에 횡단보도 또는 crosswalk
    tts_name = None
    for det in detections:
        if not isinstance(det, dict):
            continue
        obj_name = det.get('object') or det.get('class')
        if obj_name in ('crosswalk', '횡단보도'):
            # 횡단보도 감지 시 TTS 생성
            text = "횡단보도가 감지되었습니다."
            tts_name = f"{uuid.uuid4().hex}.mp3"
            tts_path = os.path.join(TTS_DIR, tts_name)
            try:
                tts = gTTS(text=text, lang="ko")
                tts.save(tts_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"TTS error: {e}")
            break

    # 8) 결과 저장
    stored_result['result'] = result
    stored_result['tts'] = tts_name

    # 9) JSON 응답: tts_url은 생성된 경우에만
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
