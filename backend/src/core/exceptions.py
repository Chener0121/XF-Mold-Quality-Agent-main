from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=404)


class DocumentProcessingError(AppException):
    def __init__(self, message: str = "文档处理失败"):
        super().__init__(message, status_code=422)


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
