import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import JSONResponse
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)


logger = logging.getLogger(__name__)


def create_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "request": {
            "id": str(uuid4()),
            "path": request.url.path,
            "method": request.method,
        },
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "status_code": status_code,
    }


def register_exception_handlers(
    app: FastAPI,
) -> None:
    @app.exception_handler(
        RequestValidationError
    )
    async def validation_error_handler(
        request: Request,
        exception: RequestValidationError,
    ):
        details = []

        for error in exception.errors():
            field = ".".join(
                str(item)
                for item in error.get("loc", [])
            )

            details.append(
                {
                    "field": field,
                    "message": error.get(
                        "msg",
                        "Invalid value",
                    ),
                    "type": error.get(
                        "type",
                        "validation_error",
                    ),
                }
            )

        content = create_error_response(
            request=request,
            status_code=422,
            code="VALIDATION_ERROR",
            message=(
                "The submitted data is invalid."
            ),
            details=details,
        )

        return JSONResponse(
            status_code=422,
            content=content,
        )

    @app.exception_handler(
        StarletteHTTPException
    )
    async def http_error_handler(
        request: Request,
        exception: StarletteHTTPException,
    ):
        error_code = (
            "RESOURCE_NOT_FOUND"
            if exception.status_code == 404
            else f"HTTP_{exception.status_code}_ERROR"
        )

        message = (
            exception.detail
            if isinstance(exception.detail, str)
            else "HTTP request failed"
        )

        content = create_error_response(
            request=request,
            status_code=exception.status_code,
            code=error_code,
            message=message,
            details=(
                None
                if isinstance(
                    exception.detail,
                    str,
                )
                else exception.detail
            ),
        )

        return JSONResponse(
            status_code=exception.status_code,
            content=content,
            headers=exception.headers,
        )

    @app.exception_handler(Exception)
    async def internal_error_handler(
        request: Request,
        exception: Exception,
    ):
        logger.exception(
            "Unhandled application error",
            exc_info=exception,
        )

        content = create_error_response(
            request=request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message=(
                "An unexpected server error occurred."
            ),
        )

        return JSONResponse(
            status_code=500,
            content=content,
        )