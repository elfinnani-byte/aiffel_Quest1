import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers.summaries import router as summaries_router

app = FastAPI(title="요약비서 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summaries_router)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PUBLIC_DIR = os.path.join(_PROJECT_ROOT, "public")


@app.get("/__debug")
def __debug():
    return {
        "file": os.path.abspath(__file__),
        "project_root": _PROJECT_ROOT,
        "public_dir": _PUBLIC_DIR,
        "public_dir_exists": os.path.isdir(_PUBLIC_DIR),
        "project_root_listing": os.listdir(_PROJECT_ROOT) if os.path.isdir(_PROJECT_ROOT) else None,
    }


if os.path.isdir(_PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=_PUBLIC_DIR, html=True), name="public")
