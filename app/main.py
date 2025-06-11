from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api_routes import router as api_router

# FastAPI 앱 객체 생성 / Create FastAPI app object
app = FastAPI(
    title="Vision Aid with Web UI",
    description="ESP32-CAM → 서버 → 웹 대시보드 / ESP32-CAM → Server → Web Dashboard",
    version="1.0.0"
)

# 1) CORS 미들웨어 등록 (모든 도메인 허용) / Register CORS middleware (Allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2) /static 경로에 정적 파일 디렉토리 연결 / Mount static directory to /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3) 루트(/)에 index.html 반환 / Serve index.html at root URL
@app.get("/", include_in_schema=False)
def serve_root():
    return FileResponse("static/index.html", media_type="text/html")

# 4) API 라우터 등록 (감지/분석 엔드포인트 제공) / Include API router (detection endpoints)
app.include_router(api_router, prefix="", tags=["detection"])
