# Inference Serving — Upload → Curvas + Detratores

> **Purpose**: API local que materializa Camada 3→5 (cenário → TSA/Carga/Extrativos + Matriz C)  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09 (FastAPI); **Shipped**: 2026-07-10; **Atualizado**: 2026-07-13  
> **Autor**: Emerson Antônio · **Fonte**: `src/serving/`; PRD §5

## When to Use

- Homologação UI (modo demonstração) até 31/08
- Bind produtivo só com `release_ok=true` (manifesto A∧B∧C)
- Validação leve online (schema/mix) antes da cascata — sem quarentena batch
- Forecast operacional e what-if direto via JSON (`/api/forecast`, `/api/predict-tsa`)

## Implementation (shipped)

Pacote: `src/serving/` · CLI: `serve run` · Config: `config/serving.yaml`

### Endpoints principais

| Rota | Função |
|------|--------|
| `POST /api/scenario/validate` | `run_validate_upload` — schema/mix leve |
| `POST /api/simulate` | `run_simulate_upload` — cascata + curvas + detratores |
| `POST /api/forecast` | Forecast operacional (ExtraTrees + `TSA_roll3`) |
| `POST /api/predict-tsa` | What-if direto (Lasso, 13 preditores) |
| `GET /api/release-status` | `load_release_context` — gate L4 |
| `GET /api/template` | Download CSV template v0 |

### Contrato cascata (`InferenceResponse`)

```python
# src/serving/schemas.py (resumo)
class InferenceResponse(BaseModel):
    mode: Literal["A", "B"]
    demo: bool
    gate_ok: bool
    model_id: str
    acceptance_run_id: str
    l2_dataset_version: str
    curves: list[CurvePoint]
    detractors: list[DetractorOut]  # max 3
    warnings: list[str]
    metrics: dict[str, float | None]
```

### Política release

```python
# src/serving/policy/release.py
assert_simulate_allowed(ctx, demo_requested=demo)
# demo=false + release_ok=false → HTTP 403
```

### Resolução de campos (forecast/predict-tsa)

`resolve_process_fields()` aplica tiers:

- **Obrigatório:** carga, kappa, prod_alcali_class, db_sgf, casca, tpc, idade
- **Tier A (proxy):** pct_ab, pct_dmg, vmi_* derivados
- **Tier B (estimado):** extrativo_at via RF serving

SSOT preditores: `src/simulation/process_specs.py` (13 colunas).

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `demo_default` | `true` | UI Marco 2 — modo demonstração |
| `demo=false` | exige `release_ok` | Release produtivo |
| `default_run_id` | serving.yaml | Candidato cascata L3/L4 |
| `audit_enabled` | `true` | SQLite call-by-call |
| `static_dir` | `web/dist` | SPA montada em `/` |
| auth | ausente MVP | Débito — rede interna apenas |

## Example Usage

1. UI envia `multipart/form-data` com arquivo + `mode` + `demo` → `/api/simulate`.
2. Formulários JSON → `/api/forecast` ou `/api/predict-tsa` (13 preditores).
3. Resposta alimenta Recharts (`curves`) e painel de detratores.
4. `GET /api/release-status` alimenta `DemoBanner` e `ReleaseBadge`.
5. Auditoria: `logs/serving_audit.db` — `scripts/audit_query.py`.

## Common Mistakes

### Wrong

Treinar no request; colocar regra de MAE na UI; hardcodar `demo=true` sem consultar release; ignorar `field_origins`/`warnings`.

### Correct

Só inferência + validação leve; treino/artefato fora do request; dual-path do ingest-engine; documentar em `docs/api/`.

## See Also

- [mode-a-b-inference.md](mode-a-b-inference.md)
- [matriz-c-detractors.md](matriz-c-detractors.md)
- [artifact-packaging.md](artifact-packaging.md)
- [../../../api/README.md](../../../api/README.md)
- frontend-react `service-layer` · `production-curves-chart`
