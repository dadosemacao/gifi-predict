from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from serving.observability.schema import ApiCallRecord

ENDPOINT_MAP: dict[tuple[str, str], str] = {
    ("POST", "/api/forecast"): "forecast",
    ("GET", "/api/forecast/status"): "forecast_status",
    ("POST", "/api/predict-tsa"): "predict_tsa",
    ("GET", "/api/predict-tsa/status"): "predict_tsa_status",
    ("POST", "/api/simulate"): "simulate",
    ("POST", "/api/scenario/validate"): "scenario_validate",
    ("GET", "/api/release-status"): "release_status",
    ("GET", "/api/template"): "template",
}


def normalize_endpoint(method: str, path: str) -> str:
    key = (method.upper(), path.split("?", 1)[0])
    if key in ENDPOINT_MAP:
        return ENDPOINT_MAP[key]
    slug = path.strip("/").replace("/", "_") or "api_root"
    return slug if slug.startswith("api") else f"api_{slug}"


def truncate_text(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def summarize_json_request(body: bytes, max_bytes: int) -> str:
    if not body:
        return "{}"
    try:
        data = json.loads(body)
        return truncate_text(json.dumps(data, ensure_ascii=False), max_bytes)
    except json.JSONDecodeError:
        return truncate_text(body.decode("utf-8", errors="replace"), max_bytes)


def _parse_content_disposition(header: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            out[key.strip().lower()] = val.strip().strip('"')
    return out


def summarize_multipart_request(
    body: bytes, content_type: str
) -> tuple[str, str | None, str | None]:
    boundary_match = re.search(r"boundary=([^;\s]+)", content_type, flags=re.I)
    if not boundary_match:
        payload = {"content_type": "multipart/form-data", "parse_error": True}
        return json.dumps(payload, ensure_ascii=False), None, None

    boundary = boundary_match.group(1).strip('"')
    delimiter = f"--{boundary}".encode()
    summary: dict[str, Any] = {"content_type": "multipart/form-data"}
    file_sha256: str | None = None
    file_name: str | None = None

    for section in body.split(delimiter):
        section = section.lstrip(b"\r\n")
        if not section or section == b"--":
            continue
        header_block, _, content = section.partition(b"\r\n\r\n")
        if not header_block:
            continue
        headers = header_block.decode("utf-8", errors="replace")
        disp = ""
        for line in headers.splitlines():
            if line.lower().startswith("content-disposition:"):
                disp = line.split(":", 1)[1].strip()
                break
        meta = _parse_content_disposition(disp)
        name = meta.get("name")
        if not name:
            continue
        if content.endswith(b"\r\n"):
            field_content = content[:-2]
        else:
            field_content = content
        if "filename" in meta:
            file_name = meta.get("filename")
            file_sha256 = hashlib.sha256(field_content).hexdigest()
            summary["file_name"] = file_name
            summary["file_sha256"] = file_sha256
        else:
            summary[name] = field_content.decode("utf-8", errors="replace")

    return json.dumps(summary, ensure_ascii=False), file_sha256, file_name


def build_request_json(
    body: bytes,
    content_type: str | None,
    max_bytes: int,
) -> tuple[str, str | None, str | None]:
    if content_type and "multipart/form-data" in content_type.lower():
        return summarize_multipart_request(body, content_type)
    return summarize_json_request(body, max_bytes), None, None


def enrich_from_response(
    record: ApiCallRecord,
    body: bytes,
    status: int,
    max_bytes: int,
) -> None:
    if not body:
        return
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        record.response_json = truncate_text(
            body.decode("utf-8", errors="replace"),
            max_bytes,
        )
        return

    record.response_json = truncate_text(json.dumps(data, ensure_ascii=False), max_bytes)
    if status >= 400:
        detail = data.get("detail")
        record.error_detail = truncate_text(json.dumps(detail, ensure_ascii=False), max_bytes)
        return

    record.product = data.get("product")
    record.model_id = data.get("model_id")
    record.family = data.get("family")
    if fo := data.get("field_origins"):
        record.field_origins_json = json.dumps(fo, ensure_ascii=False)
    if warnings := data.get("warnings"):
        record.warnings_json = json.dumps(warnings, ensure_ascii=False)
    if metrics := data.get("metrics"):
        record.metrics_json = json.dumps(metrics, ensure_ascii=False)

    if record.mode is None and (mode := data.get("mode")) is not None:
        record.mode = str(mode)
    if record.row_count is None and (rc := data.get("row_count")) is not None:
        record.row_count = int(rc)


def client_ip_from_scope(scope: dict) -> str | None:
    client = scope.get("client")
    if client and isinstance(client, (list, tuple)) and client:
        return str(client[0])
    return None


def header_value(scope: dict, name: str) -> str | None:
    headers = scope.get("headers") or []
    target = name.lower().encode()
    for key, val in headers:
        if key.lower() == target:
            return val.decode("utf-8", errors="replace")
    return None
