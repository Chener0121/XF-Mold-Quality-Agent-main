from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.exceptions import AppException, app_exception_handler
from src.core.logger import setup_logging
from src.core.middleware import logging_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()

    from src.models.entities.document import Base
    from src.core.dependencies import engine
    import src.models.entities.conversation  # noqa: F401
    import src.models.entities.chunk  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="XF模具智能体平台 - 后端API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)
app.add_exception_handler(AppException, app_exception_handler)

app.include_router(api_router, prefix=settings.API_PREFIX)
