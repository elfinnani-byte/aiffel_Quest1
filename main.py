from fastapi.staticfiles import StaticFiles

from backend.app import app

app.mount("/", StaticFiles(directory="public", html=True), name="public")
