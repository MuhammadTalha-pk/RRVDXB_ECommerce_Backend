from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
)


async def rate_limit_exceeded_handler(
    request: Request,
    exception: RateLimitExceeded,
):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": (
                    "Too many requests. "
                    "Please try again later."
                ),
                "details": str(exception.detail),
            },
            "request": {
                "id": str(uuid4()),
                "path": request.url.path,
                "method": request.method,
            },
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "status_code": 429,
        },
        headers={
            "Retry-After": "60",
        },
    )


def configure_rate_limiter(
    app: FastAPI,
) -> None:
    app.state.limiter = limiter

    app.add_exception_handler(
        RateLimitExceeded,
        rate_limit_exceeded_handler,
    )