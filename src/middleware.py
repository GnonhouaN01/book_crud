import logging
from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send


logger = logging.getLogger("bookly.requests")
logger.setLevel(logging.INFO)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = perf_counter()
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")
        client = scope.get("client")
        client_address = f"{client[0]}:{client[1]}" if client else "unknown"

        async def send_with_logging(message: Message) -> None:
            if message["type"] == "http.response.start":
                await send(message)
                elapsed_ms = (perf_counter() - started_at) * 1000
                logger.info(
                    "%s %s %s %s completed in %.2f ms",
                    client_address,
                    method,
                    path,
                    message["status"],
                    elapsed_ms,
                )
                return
            await send(message)

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "%s %s %s 500 failed after %.2f ms",
                client_address,
                method,
                path,
                elapsed_ms,
            )
            raise
