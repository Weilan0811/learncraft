from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assets import router as assets_router
from app.api.content_generation import router as content_generation_router
from app.api.learning import router as learning_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Extensible skeleton for multimodal content generation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "content-generator-agent"}


app.include_router(content_generation_router, prefix="/api/content-generation", tags=["content-generation"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(learning_router, prefix="/api", tags=["learning"])
