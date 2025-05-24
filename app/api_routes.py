# app/api_routes.py

import os
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.ai_model import analyze_image  # 이미지 경로를 받아 분석 결과를 반환하는 함수

router = APIRouter()
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze_image")
async def analyze_image_endpoint(request: Request):
    # 1) Content-Type 검사
    if request.headers.get("content-type") != "application/octet-stream":
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    # 2) 바디(raw bytes) 읽기
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    # 3) 임시 파일로 저장
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(body)

    # 4) AI 모델 분석
    try:
        result = analyze_image(filepath)  # 예: "횡단보도 감지됨" 또는 dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference error: {e}")

    # 5) JSON으로 분석 결과 반환
    return JSONResponse({"result": result})
