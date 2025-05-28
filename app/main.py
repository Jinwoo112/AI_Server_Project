from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api_routes import router as api_router

app = FastAPI(
    title="Vision Aid with Web UI",
    description="ESP32-CAM → 서버 → 웹 대시보드",
    version="1.0.0"
)

# 1) CORS (API 호출용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2) /static 경로에 static 디렉터리 매핑
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3) 루트(/)에 index.html 리턴
@app.get("/", include_in_schema=False)
def serve_root():
    return FileResponse("static/index.html", media_type="text/html")

# 4) API 라우터 등록 (/analyze_image, /latest_detection, /latest_tts 등)
app.include_router(api_router, prefix="", tags=["detection"])
