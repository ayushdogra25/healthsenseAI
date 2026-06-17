import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.database.connection import engine, Base
from backend.routes import auth, predict, history, profile, reports, admin

# Create static directories if they don't exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "reports"), exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Personalized Health Guidance Assistant API",
    version="1.0.0"
)

# Configure CORS
allowed_origins = ["*"] if settings.DEBUG else settings.cors_origin_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder to serve PDFs
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(profile.router)
app.include_router(reports.router)
app.include_router(admin.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "debug": settings.DEBUG,
        "environment": settings.ENVIRONMENT,
    }

frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
