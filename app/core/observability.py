import logging
import time
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session


class RequestLoggingMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app
        self.logger = logging.getLogger("app.access")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        request = Request(scope, receive=receive)
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or f"req_{int(time.time() * 1000)}"
        request.state.request_id = request_id
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            self.logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else None,
                },
            )


def check_database_readiness(db: Session) -> bool:
    db.execute(text("SELECT 1"))
    return True
