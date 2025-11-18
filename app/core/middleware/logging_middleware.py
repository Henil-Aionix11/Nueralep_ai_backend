# app/core/middleware/logging_middleware.py
import json
import random
import time
import uuid
from collections.abc import Callable
from typing import Any, ClassVar

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import config_manager
from app.core.config.types import LoggingMiddlewareConfig


class LoggingMiddleware(BaseHTTPMiddleware):
    METHODS_WITH_BODY: ClassVar[set[str]] = {"POST", "PUT", "PATCH"}
    SENSITIVE_FIELDS: ClassVar[set[str]] = {
        "password",
        "token",
        "secret",
        "key",
        "auth",
        "credential",
    }
    SENSITIVE_HEADERS: ClassVar[set[str]] = {"authorization", "cookie", "x-api-key"}

    def __init__(self, app: Any, config: LoggingMiddlewareConfig | None = None) -> None:
        super().__init__(app)
        self.config = config or config_manager.get_config("logging_middleware_config")
        self.default_sample_rate = self.config.default_sample_rate
        logger.info(
            "Initialized logging middleware",
            payload={
                "default_sample_rate": self.default_sample_rate,
                "route_configs": {
                    path: {
                        "sample_rate": cfg.sample_rate,
                        "description": cfg.description,
                    }
                    for path, cfg in self.config.routes.items()
                },
            },
        )

    def should_log_request(self, path: str) -> bool:
        for route_pattern, config in self.config.routes.items():
            if route_pattern.endswith("*"):
                if path.startswith(route_pattern[:-1]):
                    return random.random() < config.sample_rate  # noqa: S311
            elif path == route_pattern:
                return random.random() < config.sample_rate  # noqa: S311
        return random.random() < self.config.default_sample_rate  # noqa: S311

    def get_safe_headers(self, request: Request) -> dict[str, str]:
        return {
            k.lower(): v
            for k, v in request.headers.items()
            if k.lower() not in self.SENSITIVE_HEADERS
        }

    def _sanitize_body(self, raw: bytes) -> dict | list | None:
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return None
        if isinstance(data, dict):
            return {
                k: ("***" if any(s in k.lower() for s in self.SENSITIVE_FIELDS) else v)
                for k, v in data.items()
            }
        return data

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # pylint: disable=too-many-locals
        if not self.should_log_request(request.url.path):
            return await call_next(request)

        start_time = time.time()
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # --- read & buffer the body ONCE ---
        raw_body = b""
        if request.method in self.METHODS_WITH_BODY:
            # This consumes the stream; we must replay it below.
            raw_body = await request.body()

        # Build a new Request that REPLAYS the same body to the next app
        async def receive() -> dict:
            nonlocal raw_body
            body = raw_body
            raw_body = b""  # ensure it is sent only once
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive=receive)

        context_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
        with logger.contextualize(**context_data):
            try:
                # Log incoming request
                log_data = {
                    "headers": self.get_safe_headers(request),
                    "query_params": dict(request.query_params),
                    "client_ip": request.client.host if request.client else "Unknown",
                }
                if raw_body:
                    body = self._sanitize_body(raw_body)
                    if body is not None:
                        log_data["body"] = body

                logger.debug("Incoming request", payload=log_data)

                # Time the actual handler execution
                handler_start = time.time()
                response = await call_next(request)
                handler_duration = int((time.time() - handler_start) * 1000)
                total_duration = int((time.time() - start_time) * 1000)

                response_log = {
                    "status_code": response.status_code,
                    "duration": {
                        "total_ms": total_duration,
                        "handler_ms": handler_duration,
                        "middleware_ms": total_duration - handler_duration,
                    },
                    "response_size": int(response.headers.get("content-length", 0)),
                }

                log_level = "INFO" if response.status_code < 400 else "WARNING"
                logger.log(
                    log_level,
                    "Request processed | "
                    f"{request.method} {request.url.path} | "
                    f"Status: {response.status_code} | "
                    f"Duration: {total_duration}ms",
                    payload=response_log,
                )

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.exception(
                    "Request failed | "
                    f"{request.method} {request.url.path} | "
                    f"Error: {e!s} | "
                    f"Duration: {duration_ms}ms",
                    payload={"error": str(e), "duration_ms": duration_ms},
                )
                raise

        return response
