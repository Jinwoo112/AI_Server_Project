from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api_routes import router

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기존 라우터 포함
app.include_router(router)

# 실시간 이미지 뷰 라우트 추가
@app.get("/view_latest", response_class=HTMLResponse)
async def view_latest():
    return """
    <html>
    <head>
        <title>ESP32-CAM 실시간 뷰</title>
        <meta http-equiv="refresh" content="2">
    </head>
    <body>
        <h1>ESP32-CAM 실시간 뷰</h1>
        <img src="/static/uploads/latest.jpg" width="640" alt="Live Feed">
    </body>
    </html>
    """
