# DESIGN: Superfície de Uso Web (Camada 5 GIFI)

> Arquitetura técnica para SPA React + FastAPI local que encapsula validação online (L2), inferência cascata (L3) e política de release (L4) — homologável em modo demo até `release_ok=true`.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | WEB_UI |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (design-agent) |
| **DEFINE** | [DEFINE_WEB_UI.md](./DEFINE_WEB_UI.md) |
| **Status** | Shipped |
| **Stack** | React 18 + TS + Vite · Tailwind + Shadcn · RHF + Zod · TanStack Query · Recharts · FastAPI + uvicorn |
| **Depends on** | Camada 2 (`ingest`), Camada 3 (`simulation`), Camada 4 (`acceptance`) shipped |

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CAMADA 5 — WEB UI (MVP local)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────┐         ┌─────────────────────────────────┐ │
│  │  web/ (Vite SPA)            │  HTTP   │  src/serving/ (FastAPI)         │ │
│  │  ─────────────────          │ ──────► │  ─────────────────────          │ │
│  │  scenario-upload            │ /api/*  │  routes/scenario.py             │ │
│  │  production-curves          │         │  routes/release.py              │ │
│  │  detractors-panel           │         │  routes/static.py (template+SPA)│ │
│  │  layout (DemoBanner)        │         │                                 │ │
│  │  services/ + schemas/       │         │  services/                      │ │
│  │  TanStack Query             │         │    validate → simulate → DTO    │ │
│  └─────────────────────────────┘         └───────────────┬─────────────────┘ │
│           ▲ dev: Vite proxy :5173→:8000                  │ import            │
│           ▲ prod: StaticFiles web/dist                   ▼                   │
│  ┌────────┴────────────────────────────────────────────────────────────────┐ │
│  │                     Python packages (monorepo venv)                        │ │
│  │  ingest.online.validator ──► ingest.online.infer_publish (ephemeral L2)   │ │
│  │  simulation.pipeline.infer + simulation.cascade.inference                 │ │
│  │  acceptance.matrices.matriz_c.top3_detractors (on-the-fly SHAP/coef)      │ │
│  │  acceptance.policy.gate + reports/acceptance/.../acceptance_report.json │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Artefatos lidos (não reimplementados):                                       │
│    template_cenario_v0.yaml · models/candidates/{run_id}/ · models/champion/  │
│    config/serving.yaml                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Path | Purpose | Maps to |
|-----------|------|---------|---------|
| **Serving config** | `config/serving.yaml` | `default_run_id`, host/port, paths L2/L4, demo default | FR-WUI-06 |
| **FastAPI app** | `src/serving/app.py` | Factory, CORS localhost, router mount | FR-WUI-02…04 |
| **Release policy** | `src/serving/policy/release.py` | Lê `acceptance_report.json`; 403 se prod bloqueado | FR-WUI-05, FR-WUI-06 |
| **Validate service** | `src/serving/services/validate.py` | I2 online sem quarentena | FR-WUI-02, FR-WUI-12 |
| **Simulate service** | `src/serving/services/simulate.py` | Upload → L2 ephemeral → L3 infer → DTO | FR-WUI-03, FR-WUI-05 |
| **Detractors service** | `src/serving/services/detractors.py` | Wrapper `top3_detractors` por linha-âncora | FR-WUI-09 |
| **Curves builder** | `src/serving/services/curves.py` | `preds` → `curves[]` | FR-WUI-08 |
| **Pydantic schemas** | `src/serving/schemas.py` | DTO normativo espelhando DEFINE | NFR-WUI-03, FR-WUI-05 |
| **Error mapper** | `src/serving/errors.py` | `INGEST_*` → HTTP 400/415 + PT-BR | FR-WUI-12 |
| **SPA shell** | `web/src/app/` | Providers, router, layout | FR-WUI-01 |
| **Scenario upload** | `web/src/features/scenario-upload/` | RHF + Zod + mutation | FR-WUI-07, FR-WUI-13 |
| **Production curves** | `web/src/features/production-curves/` | Recharts presentational | FR-WUI-08 |
| **Detractors panel** | `web/src/features/detractors-panel/` | Top-3 lista ordenada | FR-WUI-09 |
| **Release header** | `web/src/components/layout/` | Badge Demo/Release, run_id, MAE | FR-WUI-10 |
| **API clients** | `web/src/services/` | fetch encapsulado | SHOULD stack |
| **Zod schema** | `web/src/schemas/scenarioSchema.ts` | Espelho `template_cenario_v0` | FR-WUI-07, AT-UI-014 |

---

## Key Decisions

### Decision 1: Monorepo layout `web/` + `src/serving/`

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #1 — onde colocar frontend vs backend HTTP.

**Choice:** SPA Vite na raiz em `web/`; pacote Python `serving` em `src/serving/` junto a `ingest`, `simulation`, `acceptance`.

**Rationale:** Convenção Vite (`npm create vite web`); Python packages permanecem sob `src/` com `pyproject.toml` existente; CI pode rodar `web/` e `tests/serving/` independentemente.

**Alternatives Rejected:**
1. `src/web/` — mistura toolchain Node dentro de árvore Python; pior DX para Vite/Shadcn CLI.
2. Next.js — SSR desnecessário para MVP localhost; PRD Marco 2 prioriza velocidade.

**Consequences:**
- Dois `package.json`/`pyproject` entry points; script `scripts/dev_ui.sh` orquestra ambos.
- Build prod copia `web/dist` servido por FastAPI.

---

### Decision 2: FastAPI como única ponte HTTP (sem subprocess na UI)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** FR-WUI SHOULD — encapsular L2/L3/L4; evitar `subprocess` de CLIs no browser.

**Choice:** Endpoints REST importam módulos Python diretamente (`validate_scenario_file`, `publish_infer_features`, `infer_dataframe`, `top3_detractors`).

**Rationale:** Mesmo venv, tipagem Pydantic, latência previsível, testes pytest sobre services sem HTTP real.

**Alternatives Rejected:**
1. Chamar `ingest`/`simulate` via Typer subprocess — overhead, parsing stdout frágil.
2. Reimplementar cascata no serving — viola fronteira Camada 3.

**Consequences:**
- `pyproject.toml` ganha deps `fastapi`, `uvicorn[standard]`, `python-multipart`.
- Entry point `serve = serving.main:cli` (ou `uvicorn serving.app:app`).

---

### Decision 3: Detratores on-the-fly via L3 explainability (linha-âncora)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #2 — pré-computados L4 vs cálculo por request.

**Choice:** Reutilizar `acceptance.matrices.matriz_c.top3_detractors` no `POST /api/simulate`, aplicado à **linha-âncora** do upload (primeira linha após sort por `linha`).

**Rationale:** Matriz C na aceite valida método; upload do usuário precisa detratores contextualizados ao cenário enviado; `explainability.json` do candidato é metadata global, não por linha.

**Alternatives Rejected:**
1. Só exibir detratores pré-computados de TC-09/10 — não responde upload real do stakeholder.
2. SHAP no browser — proibido por KB (`no-business-in-ui`, latência).

**Consequences:**
- Latência +200–800 ms por request (TreeExplainer); aceitável dentro NFR p95 < 10s.
- UI cacheia resultado via TanStack Query (`queryKey: ["simulate", fileHash, mode, runId]`).
- Multi-linha: curvas exibem todas as linhas; detratores referem-se à linha-âncora (documentado no tooltip UI).

---

### Decision 4: Dual dev/prod serving (Vite proxy vs StaticFiles)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #3.

**Choice:**
- **Dev:** `vite dev` (:5173) com proxy `/api` → `uvicorn serving.app:app` (:8000).
- **Prod local:** `npm run build` + FastAPI monta `web/dist` em `/` com fallback SPA (`html=True`).

**Rationale:** HMR no frontend; homologação stakeholder com um único processo (`uvicorn` only).

**Alternatives Rejected:**
1. Só StaticFiles em dev — perde HMR.
2. Dois hosts sem proxy — CORS extra desnecessário em localhost.

**Consequences:**
- `web/vite.config.ts` define `server.proxy['/api']`.
- `ServingSettings.static_dir` aponta `web/dist` (opcional em dev).

---

### Decision 5: L2 ephemeral por request (`ui-{uuid}`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** Dual-path ingest — online sem quarentena batch; evitar poluir `data/l2/scenarios/` com uploads de demo.

**Choice:** Cada simulate gera `cenario_id = ui-{uuid4}` sob `l2/scenarios/`; manifest mínimo; **sem** publicação batch. Opcional: cleanup async de dirs > 24h (COULD no BUILD).

**Rationale:** Reutiliza `publish_infer_features` e `run_infer_pipeline` sem fork de código; path compatível com `infer_features.parquet` esperado.

**Alternatives Rejected:**
1. Inferência in-memory sem Parquet — exigiria refactor de `run_infer_pipeline`.
2. Publicação batch completa — viola SLA online e sem remediação humana.

**Consequences:**
- Disco pode acumular cenários UI; script de limpeza documentado em README.
- `l2_dataset_version` na resposta vem do `acceptance_report`, não do upload efêmero.

---

### Decision 6: Gate policy — demo explícito vs prod bind

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** FR-WUI MUST — respeitar `demo_mode` / `release_ok`; 403 quando prod bloqueado.

**Choice:**

| Condição | Comportamento |
|----------|---------------|
| `acceptance_report.demo_mode=true` | Simulate permitido; modelo = `models/candidates/{run_id}/`; resposta `demo=true` |
| `release_ok=true` e `demo=false` (form/query) | Modelo = `models/champion/{run_id}/` via **`load_production_champion_pipes`** (lê `current_champion.json`, **não** `load_champion_pipes`) |
| `release_ok=false` e `demo=false` | HTTP **403** `{ "detail": "production_bind_blocked", "release_ok": false }` |

**Rationale:** Espelha `acceptance.policy.gate.GateResult`; UI nunca mascara demo.

**Alternatives Rejected:**
1. Flag demo só no frontend — inseguro; API é autoridade.
2. Ignorar `demo=false` no MVP — viola AT-UI-006.

**Consequences:**
- Header UI lê `GET /api/release-status` (staleTime 60s).
- Banner Demo renderizado quando `releaseStatus.demo_mode === true`.

---

### Decision 7: Zod manual espelhando template v0 (sem codegen no MVP)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** FR-WUI-07, AT-UI-014 — paridade front/back.

**Choice:** `web/src/schemas/scenarioSchema.ts` mantido manualmente alinhado a `docs/kb/gifi-domain/specs/template_cenario_v0.yaml`; backend permanece autoridade via `ScenarioValidator`.

**Rationale:** Template v0 estável para Marco 2; codegen YAML→Zod é COULD futuro.

**Alternatives Rejected:**
1. Validar só no backend — UX pior (round-trip desnecessário).
2. Duplicar lógica de mix/faixas no JSX — viola `no-business-in-ui`.

**Consequences:**
- Bump de `schema_version` exige PR dual (YAML + Zod + teste AT-UI-014).

---

### Decision 8: Testes RTL + MSW (sem Playwright no BUILD)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #5.

**Choice:** Vitest + Testing Library + MSW para happy path, erro validação, banner demo; pytest para API services e gate 403.

**Rationale:** Cobertura AT-UI-001/004/005/014 sem flakiness E2E; Playwright COULD pós-Marco 2.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `config/serving.yaml` | Create | Host, port, `default_run_id`, paths | @python-developer | — |
| 2 | `src/serving/__init__.py` | Create | Package marker | @python-developer | — |
| 3 | `src/serving/config.py` | Create | `ServingSettings` (pydantic-settings) | @python-developer | 1 |
| 4 | `src/serving/schemas.py` | Create | DTOs Pydantic (`InferenceResponse`, etc.) | @python-developer | — |
| 5 | `src/serving/errors.py` | Create | Map `INGEST_*` / `ValueError` → HTTPException | @gifi-ingest-engineer | — |
| 6 | `src/serving/policy/release.py` | Create | Load report, resolve run_id, gate check | @gifi-acceptance-engineer | 3 |
| 6b | `src/serving/policy/champion_loader.py` | Create | `load_production_champion_pipes` ← `current_champion.json` | @gifi-acceptance-engineer | 3 |
| 7 | `src/serving/services/validate.py` | Create | Validate-only wrapper | @gifi-ingest-engineer | 5 |
| 8 | `src/serving/services/curves.py` | Create | Build `curves[]` from preds + labels | @gifi-simulation-engineer | 4 |
| 9 | `src/serving/services/detractors.py` | Create | Wrap `top3_detractors` | @gifi-simulation-engineer | — |
| 10 | `src/serving/services/simulate.py` | Create | Orquestra validate → L2 → infer → DTO | @gifi-simulation-engineer | 6–9 |
| 11 | `src/serving/routes/scenario.py` | Create | `POST /api/scenario/validate`, `/api/simulate` | @python-developer | 7, 10 |
| 12 | `src/serving/routes/release.py` | Create | `GET /api/release-status` | @gifi-acceptance-engineer | 6 |
| 13 | `src/serving/routes/static.py` | Create | `GET /api/template`, StaticFiles SPA | @python-developer | 3 |
| 14 | `src/serving/app.py` | Create | FastAPI factory + routers | @python-developer | 11–13 |
| 15 | `src/serving/main.py` | Create | uvicorn CLI entry | @python-developer | 14 |
| 16 | `pyproject.toml` | Modify | deps FastAPI; script `serve`; coverage `serving` | @python-developer | — |
| 17 | `tests/serving/conftest.py` | Create | Fixtures AT-006/007, temp L2 | @test-generator | — |
| 18 | `tests/serving/test_validate.py` | Create | AT-UI-003/004/011 | @test-generator | 7 |
| 19 | `tests/serving/test_simulate.py` | Create | AT-UI-001/002/008/010 | @test-generator | 10 |
| 20 | `tests/serving/test_gate_policy.py` | Create | AT-UI-006/007 | @test-generator | 6 |
| 21 | `web/package.json` | Create | React, Vite, deps stack | @react-frontend-architect | — |
| 22 | `web/vite.config.ts` | Create | Proxy `/api`, alias `@/` | @react-frontend-architect | 21 |
| 23 | `web/tsconfig.json` | Create | strict, paths | @react-frontend-architect | 21 |
| 24 | `web/tailwind.config.js` | Create | Tailwind + Shadcn preset | @react-frontend-architect | 21 |
| 25 | `web/index.html` | Create | SPA shell | @react-frontend-architect | — |
| 26 | `web/src/main.tsx` | Create | Bootstrap React | @react-frontend-architect | 27 |
| 27 | `web/src/app/providers.tsx` | Create | QueryClientProvider | @react-frontend-architect | — |
| 28 | `web/src/app/App.tsx` | Create | Router + layout | @react-frontend-architect | 29–31 |
| 29 | `web/src/components/layout/AppShell.tsx` | Create | Shell + outlet | @react-frontend-architect | 30, 31 |
| 30 | `web/src/components/layout/DemoBanner.tsx` | Create | Banner demo obrigatório | @react-frontend-architect | — |
| 31 | `web/src/components/layout/ReleaseBadge.tsx` | Create | run_id, MAE, campeões | @react-frontend-architect | 38 |
| 32 | `web/src/components/ui/*` | Create | Shadcn: button, card, input, label, alert, badge, table | @react-frontend-architect | 24 |
| 33 | `web/src/features/scenario-upload/ScenarioUploadPage.tsx` | Create | Container route | @react-frontend-architect | 34–36 |
| 34 | `web/src/features/scenario-upload/ScenarioUploadForm.tsx` | Create | Presentational form | @react-frontend-architect | 40 |
| 35 | `web/src/features/scenario-upload/useScenarioSubmit.ts` | Create | Mutation + mode | @react-frontend-architect | 37 |
| 36 | `web/src/features/scenario-upload/index.ts` | Create | Public exports | @react-frontend-architect | — |
| 37 | `web/src/services/scenarioApi.ts` | Create | validate + simulate multipart | @react-frontend-architect | 42 |
| 38 | `web/src/services/releaseApi.ts` | Create | release-status | @react-frontend-architect | 42 |
| 39 | `web/src/schemas/scenarioSchema.ts` | Create | Zod v0 (from template) | @react-frontend-architect | @gifi-domain-specialist |
| 40 | `web/src/types/inference.ts` | Create | TS types espelhando DTO | @react-frontend-architect | — |
| 41 | `web/src/lib/errorMessages.ts` | Create | `INGEST_*` → PT-BR | @react-frontend-architect | — |
| 42 | `web/src/features/production-curves/CurvesChart.tsx` | Create | Recharts presentational | @react-frontend-architect | — |
| 43 | `web/src/features/production-curves/ProductionCurvesPanel.tsx` | Create | Container curvas | @react-frontend-architect | 42 |
| 44 | `web/src/features/detractors-panel/DetractorsPanel.tsx` | Create | Top-3 lista | @react-frontend-architect | — |
| 45 | `web/src/features/scenario-upload/scenarioUpload.test.tsx` | Create | AT-UI-005, happy/error paths | @test-generator | MSW |
| 46 | `web/vitest.config.ts` | Create | Vitest + jsdom | @test-generator | — |
| 47 | `web/src/test/setup.ts` | Create | RTL + MSW handlers | @test-generator | — |
| 48 | `scripts/dev_ui.sh` | Create | uvicorn + vite paralelo | @python-developer | 14, 22 |

**Total Files:** 48

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @react-frontend-architect | 21–36, 40–44 | Stack Camada 5, feature folders, Query/RHF |
| @python-developer | 1–5, 11, 13–16, 48 | FastAPI wiring, config, entry points |
| @gifi-ingest-engineer | 5, 7 | Validacao online I2, sinais INGEST_* |
| @gifi-simulation-engineer | 8–10 | Cascata infer, curves, detractors |
| @gifi-acceptance-engineer | 6, 12, 20 | Gate policy, release-status, champion bind |
| @gifi-domain-specialist | review 39 | Template v0, Modo A/B parity |
| @test-generator | 17–20, 45–47 | AT-UI-* pytest + Vitest |

**Agent Discovery:** `.cursor/agents/*.md`, skills GIFI + `react-frontend-architect`

---

## Code Patterns

### Pattern 1: FastAPI simulate endpoint (orquestração)

```python
# src/serving/routes/scenario.py — wire validate + infer + gate

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from serving.policy.release import assert_simulate_allowed, load_release_context
from serving.schemas import InferenceResponse, ValidateResponse
from serving.services.simulate import run_simulate_upload
from serving.services.validate import run_validate_upload

router = APIRouter(prefix="/api", tags=["scenario"])


@router.post("/scenario/validate", response_model=ValidateResponse)
async def validate_scenario(
    file: Annotated[UploadFile, File()],
    mode: Annotated[Literal["A", "B"], Form()] = "A",
) -> ValidateResponse:
    return await run_validate_upload(file, mode=mode)


@router.post("/simulate", response_model=InferenceResponse)
async def simulate(
    file: Annotated[UploadFile, File()],
    mode: Annotated[Literal["A", "B"], Form()] = "A",
    demo: Annotated[bool, Form()] = True,
    run_id: Annotated[str | None, Form()] = None,
) -> InferenceResponse:
    ctx = load_release_context(run_id)
    assert_simulate_allowed(ctx, demo_requested=demo)
    cenario_id = f"ui-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (file.filename or "upload.csv")
        path.write_bytes(await file.read())
        return run_simulate_upload(
            path,
            cenario_id=cenario_id,
            mode=mode,
            release_ctx=ctx,
            demo=demo,
        )
```

### Pattern 2: Simulate service (reuse L2/L3/L4)

```python
# src/serving/services/simulate.py

from __future__ import annotations

from pathlib import Path

import pandas as pd

from acceptance.matrices.matriz_c import top3_detractors
from ingest.online.infer_publish import publish_infer_features
from simulation.cascade.inference import infer_dataframe
from simulation.config import SimulationSettings
from simulation.package.publisher import load_candidate_pipes_by_run_id

from serving.policy.champion_loader import load_production_champion_pipes
from serving.schemas import DetractorOut, InferenceResponse
from serving.services.curves import build_curves
from serving.services.detractors import build_elo3_explain_row


def run_simulate_upload(
    path: Path,
    *,
    cenario_id: str,
    mode: str,
    release_ctx,
    demo: bool,
) -> InferenceResponse:
    sim_settings = SimulationSettings.from_yaml()
    publish_infer_features(path, cenario_id)

    if demo or not release_ctx.release_ok:
        pipes, feature_cols, pointer = load_candidate_pipes_by_run_id(
            sim_settings.models_path, release_ctx.run_id
        )
    else:
        pipes, feature_cols, pointer = load_production_champion_pipes(
            sim_settings.models_path
        )

    infer_path = sim_settings.l2_path / "scenarios" / cenario_id / "infer_features.parquet"
    df = pd.read_parquet(infer_path)
    preds = infer_dataframe(
        df, mode, pipes, feature_cols, db_proxy_factor=sim_settings.db_proxy_factor
    )

    merged = df.copy()
    for col in ("TSA_dia", "Carga_Alcalina", "Extrativo_AT"):
        if col in preds.columns:
            merged[col] = preds[col].values
    if "Volume" in merged.columns and "Volume_m3" not in merged.columns:
        merged["Volume_m3"] = merged["Volume"]

    anchor_idx = merged.sort_values("linha").index[0]
    x_row = build_elo3_explain_row(merged.loc[[anchor_idx]], feature_cols["elo3"])
    family = pointer.get("champions", {}).get("elo3", "unknown")
    detractors = top3_detractors(
        pipes["elo3"], family, x_row, feature_cols["elo3"]
    )

    return InferenceResponse(
        mode=mode.upper(),
        demo=demo or release_ctx.demo_mode,
        gate_ok=release_ctx.release_ok,
        model_id=release_ctx.run_id,
        acceptance_run_id=release_ctx.run_id,
        l2_dataset_version=release_ctx.l2_dataset_version,
        curves=build_curves(merged),
        detractors=[DetractorOut(**d) for d in detractors],
        warnings=[],
        metrics={"mae_tsa_holdout": release_ctx.mae_tsa_holdout},
    )
```

### Pattern 3: Gate policy (403 prod blocked)

```python
# src/serving/policy/release.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from serving.config import ServingSettings


@dataclass(frozen=True)
class ReleaseContext:
    run_id: str
    release_ok: bool
    demo_mode: bool
    l2_dataset_version: str
    mae_tsa_holdout: float | None
    champions: dict[str, str]
    report_path: Path


def load_release_context(run_id: str | None = None) -> ReleaseContext:
    settings = ServingSettings.from_yaml()
    rid = run_id or settings.default_run_id
    if not rid:
        raise HTTPException(503, detail="default_run_id_not_configured")
    report_path = settings.reports_root / rid / "acceptance_report.json"
    if not report_path.exists():
        raise HTTPException(404, detail=f"acceptance_report_not_found:{rid}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ma = report.get("matriz_a", {})
    return ReleaseContext(
        run_id=rid,
        release_ok=bool(report.get("release_ok")),
        demo_mode=bool(report.get("demo_mode")),
        l2_dataset_version=report.get("l2_dataset_version", ""),
        mae_tsa_holdout=ma.get("mae_tsa_cascade"),
        champions=report.get("l3_champions", {}),
        report_path=report_path,
    )


def assert_simulate_allowed(ctx: ReleaseContext, *, demo_requested: bool) -> None:
    if not demo_requested and not ctx.release_ok:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "production_bind_blocked",
                "release_ok": False,
                "demo_mode": ctx.demo_mode,
            },
        )
```

### Pattern 4: Service layer + TanStack Query (frontend)

```ts
// web/src/services/scenarioApi.ts

import type { InferenceResponse, ValidateResponse } from "@/types/inference"

export async function validateScenario(file: File, mode: "A" | "B"): Promise<ValidateResponse> {
  const body = new FormData()
  body.append("file", file)
  body.append("mode", mode)
  const res = await fetch("/api/scenario/validate", { method: "POST", body })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.code ?? err.detail ?? "validate_failed")
  }
  return res.json()
}

export async function simulateScenario(
  file: File,
  mode: "A" | "B",
  demo = true,
): Promise<InferenceResponse> {
  const body = new FormData()
  body.append("file", file)
  body.append("mode", mode)
  body.append("demo", String(demo))
  const res = await fetch("/api/simulate", { method: "POST", body })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.code ?? err.detail ?? "simulate_failed")
  }
  return res.json()
}
```

```tsx
// web/src/features/scenario-upload/useScenarioSubmit.ts

import { useMutation } from "@tanstack/react-query"
import { simulateScenario } from "@/services/scenarioApi"

export function useScenarioSubmit() {
  return useMutation({
    mutationFn: ({ file, mode }: { file: File; mode: "A" | "B" }) =>
      simulateScenario(file, mode, true),
  })
}
```

### Pattern 5: Demo banner (presentational)

```tsx
// web/src/components/layout/DemoBanner.tsx

type Props = { demoMode: boolean }

export function DemoBanner({ demoMode }: Props) {
  if (!demoMode) return null
  return (
    <div role="status" className="bg-amber-100 border-amber-400 border px-4 py-2 text-sm">
      Modo demonstração — não homologado para uso operacional. Resultados usam candidato L3
      sem bind produtivo (release_ok=false).
    </div>
  )
}
```

### Pattern 6: Configuration

```yaml
# config/serving.yaml
host: "127.0.0.1"
port: 8000
default_run_id: "2026-07-10T10:54:42.849161Z"  # último candidato empacotado; override via env
reports_root: "reports/acceptance"
static_dir: "web/dist"
template_path: "docs/kb/gifi-domain/specs/template_cenario_v0.yaml"
cors_origins:
  - "http://127.0.0.1:5173"
  - "http://localhost:5173"
demo_default: true
ephemeral_prefix: "ui-"
```

---

## Data Flow

```text
1. Usuário abre SPA → GET /api/release-status
   │
   ▼
2. Header renderiza badge Demo/Release + run_id + MAE (Query staleTime 60s)
   │
   ▼
3. Upload CSV/XLSX + seleção Modo A/B
   │
   ├──► (opcional) POST /api/scenario/validate
   │         ingest.online.validator → 200 | 400 INGEST_*
   │
   ▼
4. POST /api/simulate (multipart: file, mode, demo)
   │
   ├──► policy: demo=false ∧ release_ok=false → 403 STOP
   │
   ├──► salvar temp → publish_infer_features → l2/scenarios/ui-{uuid}/
   │
   ├──► load pipes (candidate | champion)
   │
   ├──► infer_dataframe → TSA/Carga/Extrativo por linha
   │
   ├──► top3_detractors (linha-âncora, elo3)
   │
   └──► InferenceResponse JSON
   │
   ▼
5. UI: ProductionCurvesPanel + DetractorsPanel + warnings
   │
   ▼
6. (SHOULD) Download JSON snapshot client-side (Blob) para evidência homologação
```

---

## Integration Points

| System | Integration | Auth |
|--------|-------------|------|
| `ingest.online.*` | Import Python | — |
| `simulation.cascade.inference` | Import Python | — |
| `simulation.package.publisher` | Load joblib candidate/champion | — |
| `acceptance.matrices.matriz_c` | SHAP/coef on-the-fly | — |
| `reports/acceptance/{run_id}/` | JSON read-only | — |
| `template_cenario_v0.yaml` | Static download + validator contract | — |
| Vite dev server | Proxy `/api` → uvicorn | localhost |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | curves builder, error mapper, gate | `tests/serving/test_*.py` | pytest | Key pure functions |
| Integration | validate/simulate HTTP | `tests/serving/test_simulate.py` | pytest + TestClient | AT-UI-001…011 |
| Gate | 403/200 prod/demo | `tests/serving/test_gate_policy.py` | pytest | AT-UI-006/007 |
| Frontend unit | upload form, banner | `scenarioUpload.test.tsx` | Vitest + RTL + MSW | AT-UI-005, AT-UI-014 |
| CI | build strict | `npm run build`, `tsc --noEmit` | Vite/tsc | NFR-WUI-03 |
| E2E | — | Manual homologação | Browser localhost | Happy path stakeholder |

**Fixtures:** Reutilizar `tests/simulation/fixtures/l2_mini/scenarios/AT-006-mini/` e `AT-007-mini/` para Modo A/B.

**Performance (`@slow`):** AT-UI-010 — 20× simulate com fixture 500 linhas; assert p95 < 10s.

---

## Error Handling

| Error Type | HTTP | Code / Signal | UI Message (PT-BR) |
|------------|------|---------------|-------------------|
| Formato inválido (.txt) | 415 | `unsupported_file` | Formato não suportado. Use CSV ou XLSX. |
| Coluna ausente | 400 | `INGEST_SCENARIO_REJECT` | Colunas obrigatórias ausentes (ver template). |
| Mix ≠ 1 | 400 | `INGEST_MIX_FAIL` | Soma do mix fora da tolerancia (deve ser 1,00). |
| Modo A com injeção | 400 | `mode_a_forbids_inject` | Modo A nao aceita Extrativo/Carga injetados. |
| Prod bloqueado | 403 | `production_bind_blocked` | Release nao homologado (A∧B∧C). Use modo demo. |
| run_id ausente | 503 | `default_run_id_not_configured` | Configure default_run_id em config/serving.yaml. |
| Candidato nao encontrado | 404 | `candidate_not_found` | Candidato L3 nao encontrado para run_id. |

Retry: **Não** em 400/403/415; **sim** em 503 transitorio (Query retry: 1).

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `host` | string | `127.0.0.1` | Bind uvicorn (localhost only MVP) |
| `port` | int | `8000` | Porta API + SPA prod |
| `default_run_id` | string | *(último candidato)* | Candidato L3 demo |
| `reports_root` | path | `reports/acceptance` | Relatorios L4 |
| `static_dir` | path | `web/dist` | Build SPA |
| `template_path` | path | `template_cenario_v0.yaml` | Download oficial |
| `demo_default` | bool | `true` | Default form simulate |
| `cors_origins` | list | vite dev URLs | CORS dev |
| `GIFI_SERVING_*` | env | — | Override pydantic-settings |

---

## Security Considerations

- Bind **127.0.0.1** apenas (NFR-WUI-05); sem exposicao cloud no Marco 2.
- Sem auth SSO; MVP homologacao presencial.
- Upload limitado a 500 linhas (`online_max_rows` ingest config).
- Validacao server-side obrigatoria; Zod e UX-only.
- Nao servir diretorios `models/`, `data/` via HTTP — apenas endpoints explicitos.
- Temp uploads em `tempfile`; nao logar conteudo de planilha.

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | JSON struct `serve_*` via wrapper (request_id, duration_ms, cenario_id, mode, demo, run_id) |
| Metrics | `duration_ms` por endpoint em log; p95 AT-UI-010/011 em CI |
| Tracing | request_id UUID por simulate; retornado no header `X-Request-Id` |
| Audit | Resposta inclui `model_id`, `acceptance_run_id`, `l2_dataset_version` (NFR-WUI-06) |

---

## Judge Review (advisory — 2026-07-10)

> Automated judge (`judge.py --phase design`) **not run**: `OPENROUTER_API_KEY` not set.
> Setup: [judge-setup.md](file:///Users/emerson.antonio/.claude/plugins/cache/agentspec/agentspec/3.2.0/docs/getting-started/judge-setup.md)

**Verdict: PASS with fixes applied** (manual cross-check against codebase)

| Severity | Finding | Resolution |
|----------|---------|------------|
| **HIGH** | `simulation.package.publisher.load_champion_pipes()` reads `current_candidate.json`, not `models/champion/` / `current_champion.json` — would break AT-UI-007 | Added `src/serving/policy/champion_loader.py` + updated Pattern 2 |
| **MEDIUM** | Detractors need elo3 row **after** cascade merge (`Carga`/`Extrativo` preditos) + `Volume_m3` alias | Added `build_elo3_explain_row` helper in detractors service |
| **MEDIUM** | Form `mode` vs coluna `modo` — ambiguidade | Validate service rejects rows where `modo` ≠ form `mode` when coluna present |
| **LOW** | `GET /api/template` — AT-UI-012 expects arquivo uploadável | Serve CSV example from `example_header_csv` in template YAML, not raw YAML |
| **LOW** | Error code `INGEST_MIX_SUM` vs template `INGEST_MIX_FAIL` | Aligned to `INGEST_MIX_FAIL` |
| **INFO** | `load_champion_pipes` naming debt in L3 — do not reuse for prod bind | Documented; serving uses dedicated loader |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | design-agent | DESIGN inicial Camada 5 |
| 1.1 | 2026-07-10 | design-agent | Judge advisory fixes: champion loader, mix signal, template CSV |
| 1.2 | 2026-07-10 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:**

```bash
/build .claude/sdd/features/DESIGN_WEB_UI.md
```

**Ordem sugerida no BUILD:**
1. Backend serving (config → services → routes → pytest)
2. Scaffold `web/` (Vite + Shadcn + providers)
3. Features upload → curvas → detratores
4. Integracao dev proxy + `scripts/dev_ui.sh`
5. Vitest + MSW; validar AT-UI-001…014

**Agentes BUILD:** `@react-frontend-architect` (owner UI), `@python-developer` (FastAPI), `@gifi-ingest-engineer`, `@gifi-simulation-engineer`, `@gifi-acceptance-engineer`, `@test-generator`
