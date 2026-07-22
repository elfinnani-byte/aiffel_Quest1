from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.summaries import router as summaries_router

app = FastAPI(title="요약비서 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summaries_router)
