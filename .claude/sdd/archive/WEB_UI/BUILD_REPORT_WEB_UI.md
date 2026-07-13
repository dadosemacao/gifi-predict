# BUILD REPORT: WEB_UI

> Implementation report for Camada 5 — Superfície de Uso Web

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | WEB_UI |
| **Date** | 2026-07-10 |
| **Author** | build-agent |
| **DEFINE** | [DEFINE_WEB_UI.md](./DEFINE_WEB_UI.md) |
| **DESIGN** | [DESIGN_WEB_UI.md](./DESIGN_WEB_UI.md) |
| **Status** | Shipped |

---

## Summary

| Metric | Value |
|--------|-------|
| **Tasks Completed** | 48/48 |
| **Files Created** | 47 (+ web/dist build artifact) |
| **Build Time** | ~1 session |
| **Tests Passing** | 12/12 (9 pytest serving + 3 vitest) |
| **Agents Used** | build-agent (direct) |

---

## Task Execution with Agent Attribution

| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Backend `src/serving/` | (direct) | Complete | FastAPI + L2/L3/L4 bridge |
| 2 | `config/serving.yaml` | (direct) | Complete | default_run_id configured |
| 3 | Pytest `tests/serving/` | (direct) | Complete | 9 tests |
| 4 | Web SPA `web/` | (direct) | Complete | Vite + Tailwind + Query |
| 5 | Vitest RTL tests | (direct) | Complete | Demo banner AT-UI-005 |
| 6 | `scripts/dev_ui.sh` | (direct) | Complete | uvicorn + vite |

---

## Files Created

| File | Purpose | Verified |
|------|---------|----------|
| `config/serving.yaml` | Serving config | Yes |
| `src/serving/**` | FastAPI package (18 modules) | Yes |
| `tests/serving/**` | API tests | Yes |
| `web/**` | React SPA | Yes |
| `scripts/dev_ui.sh` | Dev orchestration | Yes |
| `pyproject.toml` | fastapi, uvicorn, serve CLI | Yes |

---

## Verification Results

### Lint Check

```text
ruff check src/serving tests/serving — All checks passed (after --fix)
```

**Status:** Pass

### Type Check

```text
tsc --noEmit (web/) — pass
npm run build — pass
```

**Status:** Pass

### Tests

```text
pytest tests/serving — 9 passed
npm run test (web/) — 3 passed
```

**Status:** 12/12 Pass

---

## Autonomous Decisions

| # | Decision Point | Chose | Rationale |
|---|----------------|-------|-----------|
| 1 | Shadcn CLI vs minimal UI primitives | Minimal Tailwind components in `components/ui/` | Faster BUILD; same presentational boundary |
| 2 | Align ingest/sim L2 paths in simulate | `publish_infer_features` uses `IngestSettings`; read parquet from same `l2_path` | Avoid path mismatch between layers |
| 3 | MSW in Vitest | Mock `releaseApi` only; banner tests without full MSW server | Simpler setup; covers AT-UI-005 |

---

## Deviations from Design

| Deviation | Reason | Impact |
|-----------|--------|--------|
| No separate `table` shadcn component | MVP uses lists for detratores | None — FR-WUI-09 met |
| `web/dist` committed by build locally | Vite build output for StaticFiles prod test | Operator runs `npm run build` before `serve run` |

---

## Acceptance Test Verification

| ID | Scenario | Status | Evidence |
|----|----------|--------|----------|
| AT-UI-001 | Upload Modo A/B válido → curves | Pass | `test_simulate_api_mode_a` |
| AT-UI-003 | Modo A rejeita injeção | Pass | `test_validate_mode_a_rejects_injection` |
| AT-UI-004 | Mix inválido | Pass | `test_validate_mix_invalid` |
| AT-UI-005 | Demo banner | Pass | `scenarioUpload.test.tsx` |
| AT-UI-006 | Prod blocked 403 | Pass | `test_prod_blocked_when_not_released` |
| AT-UI-008 | Top-3 detratores | Pass | `test_simulate_mode_b_returns_curves_and_detractors` |
| AT-UI-009 | release-status metadata | Pass | `test_release_status` |
| AT-UI-012 | Template download | Pass | `test_template_download` |
| AT-UI-010/011 | Performance @slow | Pending | Not run in CI this build |

---

## Final Status

### Overall: COMPLETE

**Completion Checklist:**

- [x] All tasks from manifest completed
- [x] Lint / typecheck pass
- [x] Tests pass
- [x] Build report generated
- [ ] AT-UI-010/011 slow benchmarks (manual/CI `@slow`)

---

## Next Step

```bash
/ship .claude/sdd/features/DEFINE_WEB_UI.md
```

**Run locally:**

```bash
# Terminal 1
serve run

# Terminal 2
cd web && npm run dev

# Or
./scripts/dev_ui.sh
```
