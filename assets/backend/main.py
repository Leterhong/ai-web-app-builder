"""AI Web App - FastAPI 入口。

启动（从项目根目录，相对导入生效）:
    PYTHONPATH=. venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

注意:
    main.py 使用相对导入（from .api import ...），必须以包形式启动，
    在 backend/ 内直接 `uvicorn main:app` 会因相对导入崩溃。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import import_routes, model_routes, ai_routes
from .storage.db import init_db

app = FastAPI(title="AI Web App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(import_routes.router, prefix="/api")
app.include_router(model_routes.router, prefix="/api")
app.include_router(ai_routes.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "name": "AI Web App"}
