from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.settings import get_settings
from fastapi.staticfiles import StaticFiles
from app.routes.analyze import router as analyze_router
from app.routes.auth import router as auth_router
from app.routes.meetings import router as meetings_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

# Mount frontend static files
import os
is_vercel = os.environ.get("VERCEL") == "1"

if not is_vercel:
    # local path resolution: root of the project where 'public' folder resides
    # We are in the_shield/backend/app/main.py, so we go up 3 levels to reach root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    public_path = os.path.abspath(os.path.join(base_dir, "public"))
    
    if os.path.exists(public_path):
        app.mount("/static", StaticFiles(directory=public_path), name="static")
        # Mount public at root (must be after routers)
        app.mount("/", StaticFiles(directory=public_path, html=True), name="static")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use '/api' prefix on Vercel to match rewrites and frontend build
api_prefix = "/api" if is_vercel else ""
app.include_router(analyze_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)
app.include_router(meetings_router, prefix=api_prefix)

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)
