#!/usr/bin/env bash
# Smoke local do container gifi-serving (AT-DSP-004…006).
# Autor: Emerson Antônio
# Data: 2026-07-14
#
# Uso (somente localhost):
#   ./scripts/smoke_serving_docker.sh
#   EXPECTED_RUN_ID='...' STRICT_RELEASE_OK=1 ./scripts/smoke_serving_docker.sh
#
# AVISO: não publicar a porta em rede corporativa/pública até autenticação (fase E).

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EXPECTED_RUN_ID="${EXPECTED_RUN_ID:-2026-07-10T10:54:42.849161Z}"
STRICT_RELEASE_OK="${STRICT_RELEASE_OK:-0}"

echo "== smoke against ${BASE_URL} (localhost only) =="

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -sfS "${BASE_URL}/api/release-status" -o "${tmp}/release.json"
curl -sfS "${BASE_URL}/api/forecast/status" -o "${tmp}/forecast.json"
curl -sfS "${BASE_URL}/api/predict-tsa/status" -o "${tmp}/tsa.json"
curl -sfS "${BASE_URL}/" -o "${tmp}/index.html"

python3 - "$tmp" "$EXPECTED_RUN_ID" "$STRICT_RELEASE_OK" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

tmp = Path(sys.argv[1])
expected_run_id = sys.argv[2]
strict = sys.argv[3] == "1"

release = json.loads((tmp / "release.json").read_text(encoding="utf-8"))
required = [
    "run_id",
    "release_ok",
    "demo_mode",
    "l2_dataset_version",
    "mae_tsa_holdout",
    "champions",
]
missing = [k for k in required if k not in release]
if missing:
    raise SystemExit(f"release-status sem campos: {missing}")

if release["run_id"] != expected_run_id:
    raise SystemExit(
        f"run_id esperado={expected_run_id!r} obtido={release['run_id']!r}"
    )

if not isinstance(release["release_ok"], bool):
    raise SystemExit("release_ok deve ser bool")

if not isinstance(release["demo_mode"], bool):
    raise SystemExit("demo_mode deve ser bool (vem do acceptance_report)")

if not isinstance(release["champions"], dict):
    raise SystemExit("champions deve ser objeto")

if strict and release["release_ok"] is not True:
    raise SystemExit(
        "STRICT_RELEASE_OK=1 exige release_ok=true "
        f"(obtido={release['release_ok']})"
    )

if release["release_ok"] is not True:
    print(
        "AVISO: release_ok=false — gate L4 não liberou bind prod; "
        "packaging smoke OK, go-live bloqueado até acceptance release_ok=true",
        file=sys.stderr,
    )
if release["demo_mode"] is True:
    print(
        "AVISO: demo_mode=true no acceptance_report "
        "(campo do relatório L4, não o demo_default do serving.yaml)",
        file=sys.stderr,
    )

html = (tmp / "index.html").read_text(encoding="utf-8", errors="replace")
if 'id="root"' not in html and "id='root'" not in html:
    if "<html" not in html.lower():
        raise SystemExit("GET / não parece SPA/HTML")

print("OK: release-status + forecast/status + predict-tsa/status + SPA /")
print(
    json.dumps(
        {
            "run_id": release["run_id"],
            "release_ok": release["release_ok"],
            "demo_mode": release["demo_mode"],
        },
        ensure_ascii=False,
    )
)
PY
