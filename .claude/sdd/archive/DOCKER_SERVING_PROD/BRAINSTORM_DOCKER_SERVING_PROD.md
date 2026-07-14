# BRAINSTORM: Docker Serving Prod (MVP container local)

> Exploração Phase 0 — empacotar Camada 5 (API + UI) em 1 container validável localmente, alinhado ao contrato futuro do Azure App Service

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | DOCKER_SERVING_PROD |
| **Date** | 2026-07-14 |
| **Author** | Emerson Antônio |
| **Status** | ✅ Shipped |
| **Facilitator** | brainstorm-agent (session Cursor) |

---

## Initial Idea

**Raw Input:** Analisar `docs/guides/AZURE_APP_SERVICE_REQUISITOS.md` e trabalhar para implementar a solução (publicar API FastAPI + SPA React em Produção no Azure App Service Linux container).

**Context Gathered:**
- Levantamento Azure (§1–14) cobre RG, App Service Plan, ACR, Files, Key Vault, VNet/PE, débitos de segurança e CI/CD — status “sem implementação”
- Tarefa irmã `docs/guides/TAREFA_DOCKER_SERVING_PROD.md` já fecha premissas: 1 container, Blob SoT + bake, volume só `logs/`, jobs locais, sem MLflow
- Repositório **sem** `Dockerfile` / compose; host default `127.0.0.1` em `config/serving.yaml`; sem `/healthz`
- Artefatos ML/`reports` tipicamente fora do Git (~25–40 MB pacote mínimo)
- Premissa de produto: um Web App serve API + SPA (`web/dist` sob FastAPI)

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `scripts/` (pack release), docs em `docs/guides/` | Packaging first; sem mudança `src/serving` neste MVP |
| Relevant KB Domains | gifi-domain (template), serving paths via `docs/kb/_index.yaml` | Imagem deve incluir KB mínima para root detect + template |
| IaC Patterns | Nenhum IaC Azure no repo | IaC/pipeline **fora** deste MVP; contrato espelhado no compose |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Resultado do primeiro ciclo? | **(a) MVP container local** — Dockerfile + compose + pacote + smoke; Azure/IaC depois | Escopo = fases A–C da tarefa Docker; D/E rastreadas como próximo ciclo |
| 2 | Origem dos artefatos ML/`reports`? | **(a) Pacote a partir do filesystem local** → `releases/{run_id}/` + `COPY` no Docker | Script de pack obrigatório; Blob upload fica documentado, não implementado |
| 3 | Mudanças em `src/serving`? | **(a) Só packaging** — healthcheck via `/api/release-status` | Sem `/healthz`, sem remediação Critical/High neste ciclo |
| 4 | Samples para grounding? | **(b)+(c)** expected API outputs + ground truth local (`models/` + `reports/acceptance`) | Smoke dos status endpoints + SPA; fixtures de resposta como oráculo |

**Minimum Questions:** 4 (ok)

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Expected API outputs | Respostas de `/api/release-status`, `/api/forecast/status`, `/api/predict-tsa/status` (ambiente local) | ≥3 | Oráculo de smoke pós-`docker compose up` |
| Ground truth artefacts | `models/` + `reports/acceptance/<run_id>/` + pointers (`current_*.json`) | 1 release local | Fonte do script `releases/{run_id}/` |
| Related specs | `docs/guides/AZURE_APP_SERVICE_REQUISITOS.md` §4; `TAREFA_DOCKER_SERVING_PROD.md` | 2 | Manifesto mínimo de paths |
| Related code | `src/serving/`, `config/serving.yaml`, `web/`, `database/serving_audit/` | N/A | Runtime a empacotar sem alteração |

**How samples will be used:**
- Validar manifesto do pacote contra paths que a API realmente lê
- Smoke checklist pós-compose (status HTTP + body coerente com release local)
- Fixtures/oráculos para testes de packaging (opcional no DEFINE)

---

## Approaches Explored

### Approach A: Release pack + multi-stage Docker + Compose ⭐ Recommended

**Description:** Script empacota `releases/{run_id}/` do FS local → Dockerfile multi-stage (Node `web/dist` + Python 3.12) COPY do pacote + app → compose 1 serviço + volume `logs` → smoke.

**Pros:**
- Alinhado ao guia Azure e à tarefa Docker
- Valida o contrato de Produção (bake + audit em volume) sem depender de Azure
- Sem mudar `src/serving`

**Cons:**
- Build depende de pacote presente no context
- Imagem inclui ~25–40 MB de artefatos + runtime

**Why Recommended:** Menor desvio do levantamento já escrito; prepara Blob/ACR no próximo ciclo sem retrabalho de contrato.

---

### Approach B: Bake direto do working tree

**Description:** Dockerfile copia `models/` e `reports/` direto da raiz do repo.

**Pros:** Menos um script.  
**Cons:** Context sujo; difícil versionar release; desalinha Blob SoT futuro.  
**Status:** Rejeitada.

---

### Approach C: Compose sem bake (mount `:ro`)

**Description:** Imagem só app+UI; modelos montados no compose.

**Pros:** Iteração rápida.  
**Cons:** Não valida contrato de Produção escolhido na Q2.  
**Status:** Rejeitada.

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A |
| **User Confirmation** | 2026-07-14 |
| **Reasoning** | MVP local com bake via pacote versionável; espelha App Service futuro |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | MVP = packing local (A–C), sem Azure neste ciclo | Entregar valor sem depender de TI/rede | Go-live completo (c) |
| 2 | Artefatos via script FS → `releases/{run_id}/` | Fonte local verificada; prepara Blob | Mount-only / bake sujo da árvore |
| 3 | Zero mudanças em `src/serving` | YAGNI; healthcheck com endpoint existente | `/healthz` + security Critical |
| 4 | 1 container API+UI; volume só `logs` | Premissa Azure + tarefa Docker | Dois containers; SQLite na imagem efêmera |
| 5 | Smoke: release-status + forecast/tsa status + SPA `/` | Samples b+c disponíveis | Suite de carga / E2E simulate |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| IaC (Bicep/Terraform) App Service/ACR/PE | Fora do MVP local | Yes — ciclo Azure |
| Pipeline CI → ACR → deploy | Sem TI/ferramenta fechada | Yes — fase D |
| `/healthz` dedicado | Packaging-only; release-status basta localmente | Yes — pré go-live |
| Auth / API key / Easy Auth | Blocker de exposição, não de packing | Yes — fase E |
| Hardening joblib / upload limits | Segurança go-live | Yes — fase E |
| Private Endpoint / Key Vault / Insights | Infra Azure | Yes |
| MLflow, scale-out, Postgres audit | Já excluídos no levantamento | Marco 2+ |
| Container Node em runtime | SPA é estático | No (no MVP) |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Architecture concept (pack → bake → compose) | ✅ | Confirmado (a) | No |
| Component / deliverables MVP | ✅ | Confirmado (a) | No |

**Minimum Validations:** 2 (ok)

---

## Suggested Requirements for /define

### Problem Statement (Draft)

O GIFI Predictee precisa de um **pacote reproduzível** (imagem Docker + pacote de release + compose) que permita validar localmente o contrato de Produção da Camada 5 (API + SPA + artefatos baked + audit em volume), antes de provisionar Azure App Service.

### Target Users (Draft)

| User | Pain Point |
|------|------------|
| Engenheiro GIFI / DS | Não há forma padrão de empacotar release + subir serving como em Prod |
| Operação / TI (ciclo seguinte) | Precisa de contrato de imagem estável para App Service |

### Success Criteria (Draft)

- [ ] Script gera `releases/{run_id}/` com paths mínimos do guia Azure §4 a partir do FS local
- [ ] `docker compose up --build` sobe `gifi-serving` em `0.0.0.0:$PORT` com SPA em `/` e APIs em `/api/*`
- [ ] Smoke OK: `/api/release-status`, `/api/forecast/status`, `/api/predict-tsa/status`, SPA `/`
- [ ] Recreate do container preserva audit SQLite via volume `logs`
- [ ] Documentação de comandos + entrada no `docs/CHANGELOG.md`
- [ ] Nenhuma alteração obrigatória em `src/serving` neste MVP

### Constraints Identified

- Python 3.12; deps nativas lightgbm/xgboost/catboost/sklearn
- Root detect exige `docs/kb/_index.yaml` na imagem
- Instância única enquanto audit for SQLite em File Share/volume
- Artefatos tipicamente gitignored — pack é pré-requisito do build

### Out of Scope (Confirmed)

- Provisionamento Azure (RG, Plan, Web App, ACR, Files, Key Vault, VNet/PE)
- Pipeline CI/CD e push ACR
- Remediação débitos Critical/High e `/healthz`
- Ingest / simulate / accept como serviços cloud 24×7
- MLflow no caminho crítico

### Deliverables Map (for Design/Build)

| ID | Artefato |
|----|----------|
| A1–A4 | Manifesto + script pack + config release (env/docs) |
| B1–B5 | Dockerfile multi-stage + `.dockerignore` + entrypoint `serve` |
| C1–C4 | `docker-compose.yml` + healthcheck + runbook smoke |
| Docs | Atualizar guia/tarefa se necessário; CHANGELOG |

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 4 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 9 |
| Validations Completed | 2 |
| Duration | ~15 min (session) |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_DOCKER_SERVING_PROD.md`

Referências de entrada:
- [`docs/guides/AZURE_APP_SERVICE_REQUISITOS.md`](../../../docs/guides/AZURE_APP_SERVICE_REQUISITOS.md)
- [`docs/guides/TAREFA_DOCKER_SERVING_PROD.md`](../../../docs/guides/TAREFA_DOCKER_SERVING_PROD.md)
