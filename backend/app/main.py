import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.assets import router as assets_router
from app.api.content_generation import router as content_generation_router
from app.api.learning import router as learning_router
from app.core.config import get_settings


settings = get_settings()

# Persist unhandled-error tracebacks so HTTP 500s remain diagnosable after
# the dev-server console window is closed.
_error_log_path = Path(settings.log_root) / "unhandled_errors.log"
_error_log_path.parent.mkdir(parents=True, exist_ok=True)
_error_logger = logging.getLogger("content_generator.errors")
_error_logger.setLevel(logging.ERROR)
if not _error_logger.handlers:
    _error_logger.addHandler(logging.FileHandler(_error_log_path, encoding="utf-8"))

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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _error_logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(content_generation_router, prefix="/api/content-generation", tags=["content-generation"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(learning_router, prefix="/api", tags=["learning"])
