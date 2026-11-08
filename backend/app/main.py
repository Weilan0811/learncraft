import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.assets import router as assets_router
from app.api.content_generation import router as content_generation_router, task_service
from app.api.learning import router as learning_router
from app.core.config import get_settings
from app.core.provider_config import (
    ProviderConfigurationError,
    describe_capability,
    masked_database_url,
)
from app.services.task_recovery import recover_interrupted_tasks


settings = get_settings()

# Persist unhandled-error tracebacks so HTTP 500s remain diagnosable after
# the dev-server console window is closed.
_error_log_path = Path(settings.log_root) / "unhandled_errors.log"
_error_log_path.parent.mkdir(parents=True, exist_ok=True)
_error_logger = logging.getLogger("content_generator.errors")
_error_logger.setLevel(logging.ERROR)
if not _error_logger.handlers:
    _error_logger.addHandler(logging.FileHandler(_error_log_path, encoding="utf-8"))

_runtime_logger = logging.getLogger("content_generator.runtime")
_runtime_logger.setLevel(logging.INFO)
if not _runtime_logger.handlers:
    _runtime_handler = logging.StreamHandler()
    _runtime_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    _runtime_logger.addHandler(_runtime_handler)
_runtime_logger.propagate = False


def _log_runtime_summary() -> None:
    """Log which providers are ready without ever printing credentials."""
    _runtime_logger.info("运行模式：%s", settings.provider_mode)
    for capability in ("text", "image", "tts"):
        description = describe_capability(settings, capability)
        log = _runtime_logger.warning if "未就绪" in description else _runtime_logger.info
        log("%s服务：%s", {"text": "文本", "image": "图片", "tts": "语音"}[capability], description)
    _runtime_logger.info("数据库：%s", masked_database_url(settings))
    _runtime_logger.info("存储目录：%s", settings.storage_root)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_runtime_summary()
    if settings.recover_interrupted_tasks:
        recovery = recover_interrupted_tasks(task_service.repository)
        if recovery["interrupted_tasks"] or recovery["reset_assets"]:
            _runtime_logger.info(
                "任务恢复：%s 个任务标记为中断，%s 个资源重试标记为失败",
                recovery["interrupted_tasks"],
                recovery["reset_assets"],
            )
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Extensible skeleton for multimodal content generation.",
    lifespan=lifespan,
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


@app.exception_handler(ProviderConfigurationError)
async def provider_configuration_error_handler(
    request: Request, exc: ProviderConfigurationError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _error_logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(content_generation_router, prefix="/api/content-generation", tags=["content-generation"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(learning_router, prefix="/api", tags=["learning"])
