# Gaps de UI e Validação — Camada 5

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Versão:** 1.0
**Escopo:** Frontend React (`web/src/`) e contrato de validação com o serving.

---

## 1. Objetivo

Registrar os gaps de produto/UX identificados na revisão de código e o estado
de remediação. Backend permanece autoritativo; a UI valida cedo para reduzir 422
e dar transparência ao usuário.

---

## 2. Gaps fechados (onda 2026-07-13)

| Gap | Antes | Depois | Evidência |
|-----|-------|--------|-----------|
| Validação Zod sem faixas oficiais | `z.coerce.number()` sem limites | Faixas espelhadas de `ProcessVariablesInput` | `web/src/schemas/processSchema.ts` |
| `PROCESS_FIELDS` duplicado | Definido em `ForecastForm.tsx` e `processSchema.ts` | SSOT único em `processSchema.ts` | `ForecastForm.tsx` importa do schema |
| `forecastSchema` duplicava campos | Lista manual de 13 campos | `processVariablesSchema.extend()` | `web/src/schemas/forecastSchema.ts` |
| `demo=true` hardcoded no upload | `simulateScenario(file, mode, true)` | Toggle respeita `release_ok` | `useScenarioSubmit.ts`, `ScenarioUploadPage.tsx` |
| `field_origins` não exibido | Ignorado na UI | `FieldOriginsPanel` em forecast + what-if | `web/src/components/inference/FieldOriginsPanel.tsx` |
| `warnings` não exibidos | Ignorados | `FieldWarnings` (com `aria-live`) nas 3 abas | `web/src/components/inference/FieldWarnings.tsx` |

### 2.1 Faixas oficiais espelhadas

| Campo | Min | Max |
|-------|-----|-----|
| `carga_alcalina` | 17,5 | 21,0 |
| `kappa` | 15,0 | 18,5 |
| `db_sgf` | 465 | 515 |
| `casca_pct` | — | 1,5 |
| `tpc` | 45 | — |

SSOT: `src/serving/schemas.py` + `docs/kb/gifi-domain/specs/operational-ranges.yaml`.

### 2.2 Política demo/prod na UI

- `release_ok=false` → checkbox "Modo demonstração" **desabilitado** e forçado (`demo=true`).
- `release_ok=true` → usuário pode desmarcar para tentar bind produtivo (`demo=false`).
- HTTP 403 (`production_bind_blocked`) tratado com mensagem PT-BR em `web/src/lib/errorMessages.ts`.

---

## 3. Gaps ainda abertos

| Gap | Severidade | Nota |
|-----|-----------|------|
| Acessibilidade parcial | Info | `aria-live` adicionado nos warnings; faltam labels/roles em toda a UI |
| E2E Playwright | Could | Não implementado (só Vitest unitário/integração) |
| Campos opcionais coerção `""`→`0` | Low | `z.coerce.number().optional()` transforma string vazia em 0 |
| Curvas com valores nulos (Modo A) | Medium | Tratamento no backend (`services/curves.py`) — ver débitos serving |

---

## 4. Cobertura de testes (Vitest)

| Teste | Arquivo |
|-------|---------|
| Faixas Zod (bordas + rejeição) | `web/src/schemas/processSchema.test.ts` |
| ForecastResultPanel mostra origins/warnings | `web/src/features/operational-forecast/operationalForecast.test.tsx` |
| Toggle demo/prod respeita release | `web/src/features/scenario-upload/scenarioUpload.test.tsx` |

Rodar: `cd web && npm test`

---

## 5. Relacionados

- [README.md](README.md) — índice das APIs
- [DICIONARIO_DADOS_SERVING_CENARIOS.md](DICIONARIO_DADOS_SERVING_CENARIOS.md)
- [../guides/SECURITY_SERVING_DEBITOS.md](../guides/SECURITY_SERVING_DEBITOS.md)
- [../kb/frontend-react/patterns/schema-validation.md](../kb/frontend-react/patterns/schema-validation.md)
