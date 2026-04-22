from __future__ import annotations

from fastapi import FastAPI

from coco_engine.api.routes.solve import router as solve_router
from coco_engine.api.routes.upload import router as upload_router


app = FastAPI(title="COCOAI Study Engine API", version="1.0.0")
app.include_router(upload_router)
app.include_router(solve_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
