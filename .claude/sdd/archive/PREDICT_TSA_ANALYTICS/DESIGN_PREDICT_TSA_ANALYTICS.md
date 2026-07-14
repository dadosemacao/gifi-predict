# DESIGN: Predict-TSA Analytics

> Opt-in analytics em `POST /api/predict-tsa`: curva de sensibilidade + top-3 por ablação local; UI What-if só renderiza.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PREDICT_TSA_ANALYTICS |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio |
| **DEFINE** | [DEFINE_PREDICT_TSA_ANALYTICS.md](./DEFINE_PREDICT_TSA_ANALYTICS.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                         Camada 5 — What-if direto                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [WhatIfDirectPanel]                                                         │
│    form processo + checkbox analytics + select variável                      │
│         │ POST /api/predict-tsa?include_analytics&sensitivity_*              │
│         ▼                                                                    │
│  ┌──────────────────────┐     ┌─────────────────────────────┐                │
│  │ routes/predict_tsa   │────▶│ services/predict_tsa        │                │
│  │ Query params + body  │     │ resolve → predict baseline  │                │
│  └──────────────────────┘     └──────────────┬──────────────┘                │
│                                              │ if include_analytics           │
│                                              ▼                                │
│                               ┌──────────────────────────────┐               │
│                               │ predict_tsa_analytics.py     │               │
│                               │  SENSITIVITY_RANGES (SSOT)   │               │
│                               │  sweep grid → pipe.predict   │               │
│                               │  ablation pool → top-3       │               │
│                               └──────────────┬───────────────┘               │
│                                              │                                │
│                                              ▼                                │
│                               PredictTsaResponse                             │
│                               (+ sensitivity, detractors, ecos)              │
│         │ exclude_none                                                        │
│         ▼                                                                    │
│  SensitivityChart (Recharts) + LocalDetractorsList                           │
│  AuditMiddleware grava response_json completo (sem schema novo)              │
│                                                                              │
│  Fora desta feature: /api/forecast · /api/simulate · Parquet L2              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `routes/predict_tsa.py` | Aceitar query params analytics; `response_model_exclude_none` | FastAPI |
| `schemas.py` | `SensitivityPoint`, `LocalDetractorOut`; campos opcionais em `PredictTsaResponse` | Pydantic v2 |
| `services/predict_tsa.py` | Orquestrar resolve → baseline → analytics opcional → disclaimer | Python |
| `services/predict_tsa_analytics.py` | Ranges SSOT, sweep, ablação, top-3 | pandas + Pipeline |
| `predictTsa.ts` / `predictTsaApi.ts` | Tipos + query string no POST | TypeScript |
| `WhatIfDirectPanel.tsx` | Toggle analytics, seletor variável, render | React + RHF |
| `SensitivityChart.tsx` | Linha `value × tsa_dia` | Recharts |
| `LocalDetractorsList.tsx` | Lista top-3 (apresentacional) | React |
| Testes pytest / Vitest | AT-PTA-001…008 | pytest, Vitest |
| Docs | Dicionário API + CHANGELOG | Markdown |

---

## Key Decisions

### Decision 1: Omitir chaves quando analytics off (não `null`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** DEFINE exigia uma convenção única para retrocompat.

**Choice:** Campos `sensitivity`, `detractors`, `sensitivity_variable`, `sensitivity_steps` são `Optional` com default `None`. Rota POST usa `response_model_exclude_none=True`. Clientes antigos não veem as chaves.

**Rationale:** Menor ruído no contrato; AT-PTA-001 testa ausência de chaves.

**Alternatives Rejected:**
1. Sempre enviar `null` — rejeitado: polui payload e quebra asserts de “contrato idêntico”.
2. Dois response models diferentes — rejeitado: complexidade desnecessária no OpenAPI.

**Consequences:**
- FE trata `result.sensitivity` / `result.detractors` como opcionais.
- `model_dump(exclude_none=True)` se serializar fora do FastAPI.

---

### Decision 2: Ranges e âncoras de ablação em módulo SSOT Python (não no FE)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** Sweep e ablação precisam das mesmas faixas oficiais; FE não deve hardcodar.

**Choice:** Constante `SENSITIVITY_RANGES` e `ABLATION_POOL` em `predict_tsa_analytics.py`, derivados de Pydantic + `operational-ranges.yaml` (ver tabela §Ranges).

**Rationale:** Uma fonte no serving; UI só escolhe nome da whitelist.

**Alternatives Rejected:**
1. Ler YAML em runtime a cada request — rejeitado nesta onda (I/O extra); pode evoluir depois.
2. Duplicar faixas no Zod só para o eixo — rejeitado: drift.

**Consequences:**
- Mudança de faixa ⇒ atualizar módulo + dicionário + testes.
- `idade` usa banda pragmática documentada (sem ge/le no Pydantic hoje).

---

### Decision 3: Pool de ablação = 7 contínuas; excluir mix/VMI/classe

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** DEFINE pedia regras para unilaterais e categóricos.

**Choice:**
- **No pool:** `carga_alcalina`, `kappa`, `db_sgf`, `casca_pct`, `tpc`, `extrativo_at`, `idade` (iguais à whitelist de sensibilidade).
- **Fora do pool:** `prod_alcali_class`, `vmi_*`, `pct_ab`, `pct_dmg` (categórico / composição — ablação por médio quebra one-hot/mix).

**Âncora:** ponto médio `(low+high)/2` da tabela de ranges (não o valor do request).  
**Δ:** `delta_tsa = tsa_ablated - tsa_dia` (baseline do request).  
**Top-3:** ordenar por `|delta_tsa|` desc; empate → ordem lexicográfica de `feature`.

**Rationale:** Ranking interpretável na demo; model-agnostic; evita cenários fisicamente inválidos (soma de mix).

**Alternatives Rejected:**
1. Ablation em todos os 13 preditores — rejeitado: VMI one-hot e mix sem renormalização.
2. Coeficientes Lasso — rejeitado no BRAINSTORM (família pode mudar).
3. Stress às bordas em vez de médio — deferido COULD.

**Consequences:**
- Top-3 nunca incluirão `pct_*` / `vmi_*` nesta versão.
- Se as 7 forem próximas, ainda retornamos exatamente 3 (as de maior |Δ|).

---

### Decision 4: Predição vetorizada (1–2 `predict` em lote)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** Meta SHOULD ≤ 2 s p95; até 31 + 7 predicts.

**Choice:** Montar `DataFrame` com todas as linhas do sweep e, em segundo lote, as linhas de ablação; `pipe.predict(frame[features])` em bloco.

**Rationale:** Overhead sklearn dominado por calls repetidas 1-linha.

**Alternatives Rejected:**
1. Loop `predict` 1-linha — pior latência.
2. Paralelismo thread — complexidade e GIL sem ganho claro.

---

### Decision 5: Tipos de detrator **separados** do `/simulate`

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** `DetractorOut.method` hoje é `shap|coef|permutation`.

**Choice:** Novo `LocalDetractorOut` com `method: Literal["local_ablation"]` só em `PredictTsaResponse`. UI: componente `LocalDetractorsList` (não reutilizar `DetractorsPanel` acoplado a `InferenceResponse`).

**Rationale:** Zero risco de regressão no contrato de cenário.

**Alternatives Rejected:**
1. Estender `DetractorOut` — rejeitado: mistura semânticas Matriz C vs what-if.
2. Reusar `CurvesChart` — rejeitado: exige `carga`/`extrativo` por ponto; criar `SensitivityChart`.

---

### Decision 6: Query params no POST — confirmado

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** A-005 do DEFINE.

**Choice:** `include_analytics: bool = False`, `sensitivity_variable: str = "db_sgf"`, `sensitivity_steps: int = 15` via `Query(...)`. Validação: se `include_analytics` e (steps∉[5,31] ou variável∉whitelist) → `HTTPException(422)`.

**Rationale:** Body permanece puro `ProcessVariablesInput`; Vite proxy encaminha query string.

---

### Decision 7: Disclaimer estendido só com analytics

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Choice:** Sem analytics: texto atual. Com analytics: anexar  

` Explicabilidade assistida (sensitivity/detractors por ablação local) — não é Matriz C e não libera o gate de release.`

**Rationale:** AT-PTA-008; evita mudar disclaimer de clientes que não pedem analytics.

---

## Ranges (SSOT de implementação)

| API key | low | high | Origem |
|---------|-----|------|--------|
| `db_sgf` | 465.0 | 515.0 | Pydantic / critical SSOT |
| `carga_alcalina` | 17.5 | 21.0 | Pydantic |
| `kappa` | 15.0 | 18.5 | Pydantic |
| `casca_pct` | 0.0 | 1.5 | low=0 (física); high=Pydantic |
| `tpc` | 45.0 | 90.0 | low=Pydantic; high=ótimo SSOT |
| `extrativo_at` | 1.0 | 3.5 | clamp típico imputer Tier B / demo |
| `idade` | 4.0 | 10.0 | banda pragmática (sem faixa Pydantic) |

`SENSITIVITY_WHITELIST = frozenset(SENSITIVITY_RANGES)`  
Default eixo: `db_sgf`.  
Grid: `numpy.linspace(low, high, num=steps)` inclusivo.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `src/serving/services/predict_tsa_analytics.py` | Create | Ranges, sweep, ablation, top-3 | @python-developer | None |
| 2 | `src/serving/schemas.py` | Modify | `SensitivityPoint`, `LocalDetractorOut`, campos opcionais response | @python-developer | None |
| 3 | `src/serving/services/predict_tsa.py` | Modify | Integrar analytics + disclaimer | @python-developer | 1, 2 |
| 4 | `src/serving/routes/predict_tsa.py` | Modify | Query params + `exclude_none` | @python-developer | 2, 3 |
| 5 | `tests/serving/test_predict_tsa_analytics.py` | Create | Unit sweep/ablation/whitelist | @test-generator | 1 |
| 6 | `tests/serving/test_predict_tsa.py` | Modify | AT-PTA-001…006, 008 API | @test-generator | 3, 4 |
| 7 | `web/src/types/predictTsa.ts` | Modify | Tipos analytics opcionais | @react-frontend-architect | 2 |
| 8 | `web/src/services/predictTsaApi.ts` | Modify | Query string no POST | @react-frontend-architect | 7 |
| 9 | `web/src/features/what-if-direct/SensitivityChart.tsx` | Create | Gráfico value×tsa | @react-frontend-architect | 7 |
| 10 | `web/src/features/what-if-direct/LocalDetractorsList.tsx` | Create | Lista top-3 | @react-frontend-architect | 7 |
| 11 | `web/src/features/what-if-direct/WhatIfDirectPanel.tsx` | Modify | UI opt-in + render | @react-frontend-architect | 8–10 |
| 12 | `web/src/features/what-if-direct/whatIfDirect.test.tsx` | Create | AT-PTA-007 smoke | @test-generator | 11 |
| 13 | `docs/api/DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md` | Modify | Contrato query + response | @code-documenter | 2 |
| 14 | `docs/CHANGELOG.md` | Modify | Entrada da feature | @code-documenter | — |
| 15 | `docs/kb/frontend-react/patterns/predict-tsa-analytics.md` | Create | Pattern UI (opcional SHOULD) | @react-frontend-architect | 9–11 |

**Total Files:** 15 (1 opcional KB)

---

## Agent Assignment Rationale

| Agent | Files | Why |
|-------|-------|-----|
| @python-developer | 1–4 | Serving / schemas / serviço |
| @test-generator | 5, 6, 12 | Pytest + Vitest ATs |
| @react-frontend-architect | 7–11, 15 | Feature folder What-if, no business in JSX |
| @code-documenter | 13–14 | Dicionário + CHANGELOG |
| @gifi-domain-specialist | Consulta | Só se faixas `idade`/`extrativo` forem contestadas |

---

## Code Patterns

### Pattern 1: Analytics helper (serving)

```python
# src/serving/services/predict_tsa_analytics.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.process_specs import PROCESS_API_TO_COLUMN

SENSITIVITY_RANGES: dict[str, tuple[float, float]] = {
    "db_sgf": (465.0, 515.0),
    "carga_alcalina": (17.5, 21.0),
    "kappa": (15.0, 18.5),
    "casca_pct": (0.0, 1.5),
    "tpc": (45.0, 90.0),
    "extrativo_at": (1.0, 3.5),
    "idade": (4.0, 10.0),
}

ABLATION_POOL: tuple[str, ...] = tuple(SENSITIVITY_RANGES.keys())
SENSITIVITY_WHITELIST = frozenset(SENSITIVITY_RANGES)


@dataclass(frozen=True)
class AnalyticsResult:
    sensitivity: list[dict[str, float]]
    detractors: list[dict[str, float | str]]
    sensitivity_variable: str
    sensitivity_steps: int


def _predict_rows(
    pipe: Pipeline,
    features: list[str],
    base_cols: dict[str, float],
    overrides: list[dict[str, float]],
) -> list[float]:
    rows = []
    for ov in overrides:
        row = dict(base_cols)
        for api_key, value in ov.items():
            row[PROCESS_API_TO_COLUMN[api_key]] = float(value)
        rows.append(row)
    frame = pd.DataFrame(rows)
    return [float(x) for x in pipe.predict(frame[features])]


def build_analytics(
    *,
    pipe: Pipeline,
    features: list[str],
    resolved_api: dict[str, float],
    tsa_dia: float,
    sensitivity_variable: str,
    sensitivity_steps: int,
) -> AnalyticsResult:
    if sensitivity_variable not in SENSITIVITY_WHITELIST:
        raise ValueError(
            f"sensitivity_variable inválida: {sensitivity_variable!r}; "
            f"use uma de {sorted(SENSITIVITY_WHITELIST)}"
        )
    if not 5 <= sensitivity_steps <= 31:
        raise ValueError("sensitivity_steps deve estar em [5, 31]")

    low, high = SENSITIVITY_RANGES[sensitivity_variable]
    grid = np.linspace(low, high, num=sensitivity_steps)
    base_cols = {PROCESS_API_TO_COLUMN[k]: float(resolved_api[k]) for k in PROCESS_API_TO_COLUMN}
    sweep_preds = _predict_rows(
        pipe,
        features,
        base_cols,
        [{sensitivity_variable: float(v)} for v in grid],
    )
    sensitivity = [
        {"value": float(v), "tsa_dia": float(p)} for v, p in zip(grid, sweep_preds, strict=True)
    ]

    abl_overrides = []
    abl_features: list[str] = []
    for feat in ABLATION_POOL:
        lo, hi = SENSITIVITY_RANGES[feat]
        abl_features.append(feat)
        abl_overrides.append({feat: (lo + hi) / 2.0})
    abl_preds = _predict_rows(pipe, features, base_cols, abl_overrides)
    ranked = sorted(
        (
            {
                "feature": f,
                "delta_tsa": float(p - tsa_dia),
                "method": "local_ablation",
            }
            for f, p in zip(abl_features, abl_preds, strict=True)
        ),
        key=lambda d: (-abs(float(d["delta_tsa"])), str(d["feature"])),
    )
    return AnalyticsResult(
        sensitivity=sensitivity,
        detractors=ranked[:3],
        sensitivity_variable=sensitivity_variable,
        sensitivity_steps=sensitivity_steps,
    )
```

### Pattern 2: Rota FastAPI

```python
@router.post("/api/predict-tsa", response_model=PredictTsaResponse, response_model_exclude_none=True)
def predict_tsa(
    body: PredictTsaRequest,
    run_id: str | None = Query(default=None),
    include_analytics: bool = Query(default=False),
    sensitivity_variable: str = Query(default="db_sgf"),
    sensitivity_steps: int = Query(default=15),
) -> PredictTsaResponse:
    ...
    return run_predict_tsa(
        body.model_dump(),
        repo_root=...,
        models_root=...,
        run_id=run_id,
        include_analytics=include_analytics,
        sensitivity_variable=sensitivity_variable,
        sensitivity_steps=sensitivity_steps,
    )
```

### Pattern 3: Cliente FE

```typescript
export type PostPredictTsaOptions = {
  includeAnalytics?: boolean
  sensitivityVariable?: string
  sensitivitySteps?: number
  runId?: string
}

export async function postPredictTsa(
  body: PredictTsaRequest,
  opts: PostPredictTsaOptions = {},
): Promise<PredictTsaResponse> {
  const qs = new URLSearchParams()
  if (opts.includeAnalytics) qs.set("include_analytics", "true")
  if (opts.sensitivityVariable) qs.set("sensitivity_variable", opts.sensitivityVariable)
  if (opts.sensitivitySteps != null) qs.set("sensitivity_steps", String(opts.sensitivitySteps))
  if (opts.runId) qs.set("run_id", opts.runId)
  const suffix = qs.toString() ? `?${qs}` : ""
  const res = await fetch(`/api/predict-tsa${suffix}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  ...
}
```

### Pattern 4: SensitivityChart (apresentacional)

```tsx
// x = value (eixo da variável), y = tsa_dia — sem regra de negócio
<LineChart data={points}>
  <XAxis dataKey="value" />
  <YAxis dataKey="tsa_dia" />
  <Line type="monotone" dataKey="tsa_dia" stroke="#0b5f8a" dot={false} />
</LineChart>
```

---

## Data Flow

```text
1. UI: submit processo (+ include_analytics, variable, steps)
   │
   ▼
2. FastAPI: valida body (Pydantic) + query whitelist/steps
   │
   ▼
3. resolve_process_fields → model_frame → tsa_dia baseline
   │
   ├─ include_analytics=false → Response sem chaves analytics
   │
   └─ true → build_analytics (sweep + ablation batch predicts)
              → preenche sensitivity, detractors, ecos
              → disclaimer estendido
   │
   ▼
4. JSON (exclude_none) → AuditMiddleware → UI render curve + top-3
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|------------------|----------------|
| `current_tsa.json` + joblib Pipeline | Filesystem load (existente) | N/A (rede interna) |
| Vite proxy `/api` → `:8000` | HTTP | N/A |
| Audit SQLite | Middleware existente | N/A — response maior ok |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | `build_analytics`, ranges, 422 ValueError | `test_predict_tsa_analytics.py` | pytest | Sweep extremos + top-3 len |
| API | AT-PTA-001…006, 008 | `test_predict_tsa.py` | TestClient | Happy + erros |
| UI | AT-PTA-007 | `whatIfDirect.test.tsx` | Vitest + mock fetch | Curva + lista visíveis |
| Perf smoke | SHOULD ≤ 2 s | marca `@pytest.mark.slow` opcional | time.perf_counter | Não bloqueia MVP |

**Asserções-chave:**
- Sem analytics: `"sensitivity" not in body`
- Com default: `body["sensitivity"][0]["value"] == 465` e `[-1]["value"] == 515`
- `detractors[*].method == "local_ablation"` e `len == 3`

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| `sensitivity_variable` inválida | `ValueError` → HTTP 422 PT-BR | No |
| `sensitivity_steps` fora [5,31] | idem | No |
| Artefato ausente | `FileNotFoundError` → 404 (existente) | No |
| Resolve incompleto | `ValueError` → 422 (existente) | No |
| Feature do pool ausente em resolved | Não deve ocorrer pós-resolve; se ocorrer → 422 | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| query `include_analytics` | bool | `false` | Liga blocos analytics |
| query `sensitivity_variable` | str | `db_sgf` | Eixo do sweep |
| query `sensitivity_steps` | int | `15` | Pontos inclusivos [5,31] |
| `SENSITIVITY_RANGES` | code const | tabela §Ranges | SSOT de low/high |
| config YAML | — | — | **Sem novas chaves** nesta onda |

---

## Security Considerations

- Sem mudança de auth (débito documentado permanece).
- Query params não aumentam superfície de path traversal.
- `sensitivity_steps` limitado a 31 evita DoS trivial por N predicts.
- Continuar sem expor paths internos além do já presente em `/status`.

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | Manter logs existentes; opcional `logger.info` com `include_analytics`, steps, variable |
| Metrics | Audit SQLite já persiste `response_json` com analytics |
| Tracing | N/A |

---

## UI Labels (PT-BR)

| API feature | Label UI |
|-------------|----------|
| `db_sgf` | DB SGF |
| `carga_alcalina` | Carga alcalina |
| `kappa` | Kappa |
| `casca_pct` | % Casca |
| `tpc` | TPC |
| `extrativo_at` | Extrativo AT |
| `idade` | Idade |

Mapa estático no FE (só presentation); valores vêm do backend.

---

## Open Questions do DEFINE — fechados

| # | Resolução |
|---|-----------|
| 1 Omitir vs null | **Omitir** (`exclude_none`) |
| 2 Ablação unilaterais / VMI | Pool = 7 contínuas; âncora = médio da faixa; VMI/mix/classe fora |
| 3 Labels PT-BR | Tabela acima; espelha `PROCESS_FIELDS` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-13 | Emerson Antônio (design-agent) | Design inicial a partir do DEFINE 1.0 |
| 1.1 | 2026-07-14 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_PREDICT_TSA_ANALYTICS.md`
