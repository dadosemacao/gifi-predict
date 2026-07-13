from __future__ import annotations

import json
import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from serving.observability.extractors import (
    build_request_json,
    client_ip_from_scope,
    enrich_from_response,
    header_value,
    normalize_endpoint,
)
from serving.observability.repository import AuditRepository
from serving.observability.schema import ApiCallRecord

logger = logging.getLogger(__name__)


class AuditMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        repository: AuditRepository,
        *,
        enabled: bool = True,
        max_body_bytes: int = 65536,
    ) -> None:
        self.app = app
        self.repository = repository
        self.enabled = enabled
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/") or not self.enabled:
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        request_body = await self._read_request_body(receive)
        request_sent = False

        async def receive_replay() -> Message:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": request_body, "more_body": False}

        status_code = 500
        response_body = bytearray()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive_replay, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000.0
            record = self._build_record(
                scope,
                request_body,
                bytes(response_body),
                status_code,
                duration_ms,
            )
            try:
                self.repository.insert(record)
            except Exception:
                logger.exception("audit_insert_failed path=%s", path)

    @staticmethod
    async def _read_request_body(receive: Receive) -> bytes:
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        return bytes(body)

    def _build_record(
        self,
        scope: Scope,
        request_body: bytes,
        response_body: bytes,
        status_code: int,
        duration_ms: float,
    ) -> ApiCallRecord:
        method = str(scope.get("method", "")).upper()
        path = str(scope.get("path", ""))
        content_type = header_value(scope, "content-type")

        request_json, file_sha256, file_name = build_request_json(
            request_body,
            content_type,
            self.max_body_bytes,
        )

        record = ApiCallRecord(
            method=method,
            path=path,
            endpoint=normalize_endpoint(method, path),
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=client_ip_from_scope(scope),
            user_agent=header_value(scope, "user-agent"),
            request_json=request_json,
            file_sha256=file_sha256,
            file_name=file_name,
        )

        if request_json and "multipart" in (content_type or "").lower():
            try:
                req_data = json.loads(request_json)
                if mode := req_data.get("mode"):
                    record.mode = str(mode)
                if run_id := req_data.get("run_id"):
                    record.run_id = str(run_id)
            except json.JSONDecodeError:
                pass

        if path.endswith("/status") and status_code < 400:
            record.product = "status"

        enrich_from_response(record, response_body, status_code, self.max_body_bytes)
        return record
