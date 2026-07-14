# Tarefa — Container Docker Serving (API + UI) para Produção

**Autor:** Emerson Antônio  
**Data:** 2026-07-14  
**Versão:** 1.1  
**Status:** Em validação local (fases A–C implementadas; D–E pendentes)  
**Origem:** Decisões de arquitetura (chat 2026-07-14) + [`AZURE_APP_SERVICE_REQUISITOS.md`](AZURE_APP_SERVICE_REQUISITOS.md)  
**Escopo:** Empacotar e validar **1 container** de Produção (FastAPI serving + SPA React) para Azure App Service.  
**Fora de escopo desta tarefa:** ingest/treino/aceite como serviços cloud 24×7; MLflow; multi-região; scale-out horizontal.

---

## 1. Contexto

O GIFI precisa publicar em Produção a Camada 5 (API + UI). O levantamento Azure já existe; faltam o **pacote de artefatos**, o **Dockerfile**, o **docker-compose** de validação local e o **fluxo de upload** (jobs locais → Blob → bake na imagem).

Premissas confirmadas:

| # | Decisão | Valor |
|---|---------|--------|
| 1 | Alvo imediato | Só Produção (**API + UI**) |
| 2 | Runtime cloud | **Azure App Service** — **1 container** |
| 3 | Artefatos ML (`models/`, `reports/`) | **Blob** = source of truth; **bake na imagem** no deploy |
| 4 | Estado mutável | **Azure Files** (ou volume local) só para `logs/` (audit SQLite) |
| 5 | Jobs (ingest / simulate / accept) | **Locais ou CI**; upload do pacote de release; **não** entram na imagem de prod |
| 6 | MLflow | **Não** no caminho crítico (ADR-003 Marco 1 — manifesto + filesystem) |
| 7 | UI | Build estático Vite (`web/dist`) **dentro** da imagem; sem container Node em runtime |

---

## 2. Arquitetura alvo (resumo)

```text
Jobs locais (ingest → simulate → accept)
        │
        ▼
Pacote de release versionado (Blob)
  models/ + reports/ + pointers  →  tag release-<run_id>
        │
        ▼
CI: npm build (web) + COPY artefatos + docker build → ACR
        │
        ▼
App Service (1 container gifi-serving)
  ├── Uvicorn + FastAPI
  ├── SPA em web/dist
  ├── models/ + reports/ (baked)
  └── logs/ → Azure Files (audit SQLite)
```

Compose local: **1 serviço** (`serving`) + **1 volume** (`logs`). Espelha o contrato do App Service.

---

## 3. Critérios de sucesso

- [ ] Imagem `gifi-serving` sobe com `serve run --host 0.0.0.0 --port ${PORT:-8000}`
- [ ] SPA responde em `/` e APIs em `/api/*`
- [ ] Smoke OK: `/api/release-status`, `/api/forecast/status`, `/api/predict-tsa/status`
- [ ] Artefatos da release batem com o `run_id` / pointers configurados
- [ ] Audit SQLite persiste após recreate do container (volume/Files)
- [ ] Documentação de pacote + Compose + checklist de deploy atualizada
- [ ] Entrada no `docs/CHANGELOG.md`

---

## 4. Tarefas (checklist executável)

### Fase A — Pacote de artefatos de release

| ID | Tarefa | Notas | Status |
|----|--------|-------|--------|
| A1 | Definir manifesto do pacote mínimo (paths da seção 4 de `AZURE_APP_SERVICE_REQUISITOS.md`) | `config/serving_release_manifest.yaml` | Feito |
| A2 | Script/comando para empacotar `releases/{run_id}/` (tar/zip) a partir do filesystem local pós-`accept` | `scripts/pack_serving_release.py` | Feito |
| A3 | Documentar upload do pacote para Azure Blob (naming: `releases/{run_id}/` ou `gifi-release-{run_id}.tar.gz`) | Ver § Runbook abaixo | Feito (doc) |
| A4 | Alinhar `config/serving.yaml` / env da release (`default_run_id`, forecast/tsa run ids, `demo_default: false` em prod) | Overlay `config/serving.docker.yaml` bakeado como `serving.yaml` na imagem | Feito |

### Fase B — Dockerfile (imagem online)

| ID | Tarefa | Notas | Status |
|----|--------|-------|--------|
| B1 | Criar `Dockerfile` multi-stage: Stage Node (`web` → `dist`) + Stage Python 3.12 | `Dockerfile` na raiz | Feito |
| B2 | Instalar app via `requirements.txt` (export de `uv`/`pyproject.toml`) + entrypoint `serve` | `pip install .` no stage runtime | Feito |
| B3 | `COPY` pacote de artefatos (models + reports) no caminho esperado pelos loaders | `COPY releases/${RELEASE_RUN_ID}/...` | Feito |
| B4 | `CMD`/`ENTRYPOINT`: `serve --host 0.0.0.0 --port ${PORT:-8000}` | Typer single-command (não `serve run`); App Service `PORT` | Feito |
| B5 | `.dockerignore` — excluir `.venv`, `web/node_modules`, notebooks, excels brutos, testes, cache | `.dockerignore` na raiz | Feito |

### Fase C — docker-compose (validação local)

| ID | Tarefa | Notas | Status |
|----|--------|-------|--------|
| C1 | Criar `docker-compose.yml` com serviço único `serving` | `127.0.0.1:8000:8000`; volume só `logs` | Feito |
| C2 | Env mínimas: `GIFI_SERVING_HOST` / override CLI; `demo_default` configurável | Overlay docker YAML; CLI host/port | Feito |
| C3 | Healthcheck apontando para `/api/release-status` (até existir `/healthz`) | Gap conhecido no guia Azure | Feito |
| C4 | Documentar comandos: `up --build`, smoke curl, `down` | § Runbook abaixo + `scripts/smoke_serving_docker.sh` | Feito |

### Fase D — Integração Azure / CI (mínimo)

| ID | Tarefa | Notas | Status |
|----|--------|-------|--------|
| D1 | Pipeline mínimo: build web → baixar pacote Blob → `docker build` → push ACR | Azure DevOps ou GitHub Actions (a definir com TI) | Pendente |
| D2 | Deploy App Service (custom container) + mount Azure Files em path de `logs/` | Instância única enquanto audit for SQLite | Pendente |
| D3 | App Settings: `PORT`/`WEBSITES_PORT`, `GIFI_SERVING_DEMO_DEFAULT=false`, run ids da release | Key Vault / Managed Identity para segredos quando houver auth | Pendente |
| D4 | Smoke pós-deploy + tag de release alinhada ao `run_id` L4 | Slot staging → swap recomendado | Pendente |

### Fase E — Débitos que bloqueiam go-live (rastreio)

Não são o núcleo do packaging, mas **bloqueiam** exposição (ver guia Azure + `SECURITY_SERVING_DEBITOS.md`):

| ID | Item | Prioridade |
|----|------|------------|
| E1 | Auth / Easy Auth / API key | Critical |
| E2 | Endpoint `/healthz` leve (sem carregar joblib) | High (ops) |
| E3 | Limites de upload e hardening de path/`joblib` | Critical/High |
| E4 | Overlay `cors_origins` para hostname prod (same-origin preferível) | Medium |

---

## 5. Responsabilidades por peça

| Peça | Responsabilidade | Onde vive |
|------|------------------|-----------|
| Jobs locais | Treinar, aceitar, gerar `run_id` | Máquina/CI — CLIs `ingest` / `simulate` / `accept` |
| Blob | Guardar pacote imutável por release | Storage Account |
| Imagem `gifi-serving` | Único runtime prod: API + UI + artefatos bakeados | ACR → App Service |
| Azure Files | Persistência `logs/serving_audit.db` | Mount no Web App |
| Compose | Validar contrato localmente (1 serviço + volume logs) | Repo (`docker-compose.yml`) |

**Não criar** containers 24×7 para `src/ingest`, `src/simulation` ou `src/acceptance` nesta tarefa.

---

## 5.1 Runbook — pack → build → smoke (localhost)

**Pré-requisito:** artefatos locais válidos sob `models/` e `reports/` (pós-jobs).

```bash
# 1) Empacotar release L4
python scripts/pack_serving_release.py --run-id '2026-07-10T10:54:42.849161Z'

# 2) Conferir/atualizar run ids em config/serving.docker.yaml

# 3) Build + up (publish apenas loopback)
export RELEASE_RUN_ID='2026-07-10T10:54:42.849161Z'
# Se a porta 8000 estiver ocupada no host: export HOST_PORT=18000
docker compose up --build -d

# 4) Smoke
./scripts/smoke_serving_docker.sh
# Com HOST_PORT alternativo:
# BASE_URL=http://127.0.0.1:18000 ./scripts/smoke_serving_docker.sh
# Opcional: exigir gate L4 verde
# STRICT_RELEASE_OK=1 ./scripts/smoke_serving_docker.sh

# 5) Down (volume serving_audit persiste)
docker compose down
```

**AVISO:** uso restrito a `http://127.0.0.1:8000`. Não publicar a porta em rede
corporativa ou internet até autenticação (fase E / `SECURITY_SERVING_DEBITOS.md`).

**Blob (próximo ciclo, não implementado):** gravar o conteúdo de
`releases/{run_id}/` (ou `gifi-release-{run_id}.tar.gz`) no Storage Account;
CI baixa no `docker build` com o mesmo `RELEASE_RUN_ID`.

---

## 6. Esboço de referência — compose

Contrato esperado (implementar em Fase C; não copiar cegamente se paths do Dockerfile mudarem):

```yaml
services:
  serving:
    build:
      context: .
      dockerfile: Dockerfile
    image: gifi-serving:local
    ports:
      - "8000:8000"
    environment:
      PORT: "8000"
      GIFI_SERVING_DEMO_DEFAULT: "false"
    volumes:
      - serving_audit:/app/logs
    command: ["serve", "run", "--host", "0.0.0.0", "--port", "8000"]
    restart: unless-stopped

volumes:
  serving_audit:
```

---

## 7. Fora de escopo (explicitamente)

- Container Node/Vite em runtime
- Separar UI e API em dois containers no App Service
- MLflow Tracking / Model Registry (revisitar ADR-003 no Marco 2+)
- Jobs de treino no Azure nesta entrega
- Migração do audit SQLite → SQL/Postgres (pré-requisito de scale-out)
- Rede Private Link / WAF (pertencem ao rollout infra; consumir requisitos do guia Azure)

---

## 8. Ordem sugerida de execução

1. **A1–A4** — fechar pacote e config de release  
2. **B1–B5** — Dockerfile + `.dockerignore`  
3. **C1–C4** — compose + smoke local  
4. **D1–D4** — ACR + App Service + Files  
5. **E*** em paralelo / gate de segurança antes de tráfego real  

---

## 9. Referências

| Documento | Uso |
|-----------|-----|
| [`AZURE_APP_SERVICE_REQUISITOS.md`](AZURE_APP_SERVICE_REQUISITOS.md) | SKUs, artefatos, persistência, segurança, CI/CD |
| [`ADR-003-manifest-vs-mlflow.md`](../adr/ADR-003-manifest-vs-mlflow.md) | Sem MLflow no MVP |
| [`DEV_ENVIRONMENT.md`](DEV_ENVIRONMENT.md) | Tooling Python/Node local |
| [`SECURITY_SERVING_DEBITOS.md`](SECURITY_SERVING_DEBITOS.md) | Blockers de exposição |
| `config/serving.yaml` + `src/serving/` | Runtime e loaders |
| `web/` | SPA (build → `web/dist`) |

---

## 10. Registro de decisões (chat)

1. Um único container online na Prod.  
2. Artefatos: Blob versionado + bake; volume só para audit.  
3. Jobs separados (locais) com upload do pacote — sem imagem de jobs em Prod nesta fase.  
4. Compose = espelho local do App Service (1 serviço), não orquestração completa das 5 camadas.
