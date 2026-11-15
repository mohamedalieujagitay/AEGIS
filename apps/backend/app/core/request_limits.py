"""Request size limit.

Requests whose body is larger than ``Settings.max_request_body_bytes`` are
rejected with 413, whether the size is declared in ``Content-Length`` or
only discovered while the body is streamed.

The streamed case cannot simply raise: FastAPI converts any exception raised
while reading a body into a generic 400. Instead the middleware ends the
read early (by reporting a disconnect to the application), discards the
application's response and sends the 413 itself.
"""

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import RequestBodyTooLargeError, error_response


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = self._declared_length(scope)
        if declared is not None and declared > self.max_body_bytes:
            await self._reject(scope, receive, send)
            return

        received = 0
        exceeded = False
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received, exceeded
            if exceeded:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    exceeded = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if exceeded:
                return  # The application's response is replaced by the 413.
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not exceeded:
                raise
        if exceeded and not response_started:
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        error = RequestBodyTooLargeError()
        response = error_response(Request(scope), error.status_code, error.code, error.message)
        await response(scope, receive, send)

    @staticmethod
    def _declared_length(scope: Scope) -> int | None:
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name == b"content-length":
                try:
                    return int(value)
                except ValueError:
                    return None
        return None
