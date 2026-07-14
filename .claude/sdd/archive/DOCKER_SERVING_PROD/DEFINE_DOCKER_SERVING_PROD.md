# DEFINE: Docker Serving Prod (MVP container local)

> Empacotar e validar localmente a Camada 5 (FastAPI + SPA) em **1 container** com artefatos baked e audit em volume, espelhando o contrato futuro do Azure App Service.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | DOCKER_SERVING_PROD |
| **Date** | 2026-07-14 |
| **Author** | Emerson Antônio |
| **Status** | ✅ Shipped |
| **Clarity Score** | 15/15 |
| **Source** | `.claude/sdd/features/BRAINSTORM_DOCKER_SERVING_PROD.md` |
| **Related guides** | `docs/guides/AZURE_APP_SERVICE_REQUISITOS.md`, `docs/guides/TAREFA_DOCKER_SERVING_PROD.md` |

---

## Problem Statement

O repositório GIFI Predict já tem serving HTTP + UI, mas **não há forma padrão e reproduzível** de empacotar uma release (modelos + reports + SPA + runtime) e subir o mesmo contrato que será usado no Azure App Service. Sem isso, cada tentativa de “rodar como produção” depende de paths locais ad hoc, e a TI não recebe uma imagem com contrato estável antes do provisioning Azure.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Engenheiro GIFI / DS | Empacota release pós-`accept` e valida serving | Não há script/manifesto + Docker padrão; build “na mão” é frágil |
| Desenvolvedor Camada 5 | Itera API/UI e precisa smoke realista | Sem compose que espelhe Prod (bake + volume `logs`) |
| TI / Ops (ciclo seguinte) | Publicará no App Service | Precisa de imagem e entrypoint previsíveis; este MVP entrega o contrato local |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Script de pack gera `releases/{run_id}/` (e/ou archive) a partir do filesystem local com o **manifesto mínimo** do guia Azure §4 |
| **MUST** | `Dockerfile` multi-stage produz imagem `gifi-serving` (Node → `web/dist` + Python 3.12 + app + artefatos baked) |
| **MUST** | Entrypoint: `serve run --host 0.0.0.0 --port ${PORT:-8000}` (compatível App Service) |
| **MUST** | `docker-compose.yml` com **1 serviço** + volume só para `logs/`; healthcheck em `GET /api/release-status` |
| **MUST** | Smoke local documentado: release-status, forecast/status, predict-tsa/status, SPA `/` |
| **MUST** | **Zero** alteração obrigatória em `src/serving` neste MVP |
| **SHOULD** | `.dockerignore` mantém context enxuto; documentar naming Blob futuro (`releases/{run_id}/` ou tarball) sem implementar upload |
| **SHOULD** | Documentar env de release (`GIFI_SERVING_DEMO_DEFAULT=false`, run ids alinhados ao pacote) |
| **SHOULD** | NFRs de packaging seguros: imagem sem `.env`/segredos; user não-root se factível sem mudar app; compose bind só em `localhost` no runbook; aviso de não exposição pública |
| **COULD** | Variante compose documentada com mount `./models`/`./reports` `:ro` (não default) |
| **COULD** | Teste automatizado mínimo do manifesto (lista de paths esperados presentes no pack) |

---

## Success Criteria

- [ ] Com run local pós-`accept`, o script de pack cria `releases/{run_id}/` contendo **100%** dos paths obrigatórios do manifesto (ver § Release Package Contract)
- [ ] `docker compose up --build` sobe `gifi-serving:local` expondo `http://localhost:8000`
- [ ] `GET /api/release-status` retorna **HTTP 200** com JSON conforme `ReleaseStatusResponse` (`src/serving/schemas.py`): campos obrigatórios `run_id`, `release_ok`, `demo_mode`, `l2_dataset_version`, `mae_tsa_holdout`, `champions`; com pack válido e `GIFI_SERVING_DEMO_DEFAULT=false`, assertar `release_ok == true` e `run_id` igual ao `default_run_id` do pack
- [ ] `GET /api/forecast/status` e `GET /api/predict-tsa/status` retornam **HTTP 200**
- [ ] `GET /` retorna a SPA (HTML do build Vite, não 404)
- [ ] Após `docker compose down` + `up` (mesmo volume nomeado), o arquivo de audit em `logs/` **persiste** (SQLite recria schema se necessário, dados de chamadas anteriores permanecem se o volume for o mesmo)
- [ ] `git diff --stat` entre a tip da feature e a base do MVP mostra **0 arquivos modificados/criados** sob `src/serving/**` (permitido: zero; qualquer patch em serving falha o critério)
- [ ] `docs/CHANGELOG.md` e runbook (guia ou seção da tarefa Docker) documentam pack → build → up → smoke → down
- [ ] Imagem/build context **não** inclui `.env`, keys ou connection strings (verificado via `.dockerignore` + inspeção do context)
- [ ] Runbook declara: validação **somente em localhost**; não publicar porta em rede corporativa/pública até fase E/auth

---

## Non-Functional Requirements (MVP packaging)

| ID | Category | Requirement | Notes |
|----|----------|-------------|-------|
| NFR-SEC-01 | Security | Nenhum segredo no layer da imagem | `.dockerignore` exclui `.env`, `*.pem`, credentials |
| NFR-SEC-02 | Security | Runbook: bind/smoke apenas `127.0.0.1`/`localhost` | Exposição = fora de escopo até auth (fase E) |
| NFR-SEC-03 | Security | Preferir USER não-root no Dockerfile se não quebrar `serve`/volume `logs` | Soft; não exige mudança em `src/serving` |
| NFR-OPS-01 | Operability | Healthcheck compose com start_period adequado a cold start joblib | Endpoint pesado aceito até `/healthz` |
| NFR-REL-01 | Reliability | Volume nomeado para `logs/` — dados audit sobrevivem recreate | AT-DSP-007 |

**Explícito:** auth, Easy Auth, rate limit, hardening `joblib`/path traversal e compliance LGPD avançada permanecem **fora** (fase E / `SECURITY_SERVING_DEBITOS.md`). Este MVP entrega packaging seguro o bastante para **dev local**, não go-live.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-DSP-001 | Pack feliz | FS local com champion/forecast/tsa/acceptance presentes | Executar script pack com `run_id` | Diretório `releases/{run_id}/` (ou archive) contém todos paths do manifesto; exit code 0 |
| AT-DSP-002 | Pack incompleto | Falta `acceptance_report.json` ou pointer crítico | Executar script pack | Exit code ≠ 0 e mensagem listando path faltante |
| AT-DSP-003 | Build imagem | Pacote release no context | `docker compose build` | Imagem `gifi-serving` criada sem erro |
| AT-DSP-004 | Smoke release-status | Compose up saudável; pack com acceptance `release_ok`; env `GIFI_SERVING_DEMO_DEFAULT=false` | `curl -sf http://localhost:8000/api/release-status` | HTTP 200; JSON com `run_id` (string, = run do pack), `release_ok: true`, `demo_mode: false`, `l2_dataset_version` (string), `champions` (objeto), `mae_tsa_holdout` (number\|null); opcionalmente `matriz_a_ok`/`matriz_b_ok`/`matriz_c_ok` |
| AT-DSP-005 | Smoke forecast/tsa status | Compose up saudável | `curl -sf` nos dois `/status` | Ambos HTTP 200 |
| AT-DSP-006 | SPA root | Compose up saudável | `curl -sf http://localhost:8000/` | Body contém marcadores de SPA/Vite (ex.: `<div id="root"` ou asset hashed) |
| AT-DSP-007 | Persistência audit | Compose up; ≥1 request `/api/*` gravada | `compose down` + `up` (mesmo volume) | `logs/serving_audit.db` (ou path configurado) ainda existe e retém rows anteriores |
| AT-DSP-008 | Bind cloud-friendly | Container rodando | Inspecionar processo / logs ou probe externo | Serviço escuta `0.0.0.0` e porta do env `PORT` (default 8000); não só `127.0.0.1` |
| AT-DSP-009 | Sem diff serving | Branch com feature vs base do MVP | `git diff --name-only <base> -- src/serving/` | Lista vazia |
| AT-DSP-010 | Sem segredos na imagem | `.dockerignore` + context de build | Inspecionar ignore rules / `docker build` context | `.env` e padrões de secret excluídos; não aparecem no context |
| AT-DSP-011 | Runbook localhost | Docs atualizados | Ler runbook de smoke | Texto exige acesso só via localhost e alerta contra exposição pública |

---

## Out of Scope

- Provisionamento Azure (RG, App Service Plan, Web App, ACR, Storage, Key Vault, VNet, Private Endpoint, DNS)
- Pipeline CI/CD (build → Blob → ACR → deploy) e slot swap
- Endpoint `/healthz`, Easy Auth / API key, hardening `joblib`/upload, CORS prod
- Alterações funcionais em `src/serving` ou `web/` além do build estático na imagem
- Containers 24×7 para ingest / simulate / accept; MLflow no caminho crítico
- Scale-out multi-réplica; migração audit SQLite → SQL/Postgres
- Suite E2E de `POST /api/simulate` / forecast / predict-tsa com payloads (smoke = status + SPA)
- Upload automático para Azure Blob (apenas documentação de naming)
- **NFRs de segurança/compliance de exposição** (auth, rate limit, hardening path/`joblib`, LGPD adicional) — rastreados em `SECURITY_SERVING_DEBITOS.md` e fase E da tarefa Docker; **não** são requisitos deste MVP de packaging. Mitigação até lá: não expor o compose/imagem em rede pública.

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Python **3.12**; deps nativas para lightgbm/xgboost/catboost/sklearn | Stage runtime precisa libs de sistema adequadas |
| Technical | Detecção de root via `docs/kb/_index.yaml` | KB mínima (e template de cenário) na imagem |
| Technical | Artefatos `models/`/`reports/` tipicamente gitignored | Pack é pré-requisito do `docker build` |
| Technical | Audit SQLite + volume único | Compose **1 réplica**; volume nomeado para `logs/` |
| Process | Packaging-only: sem mudanças obrigatórias em `src/serving` | Healthcheck usa `/api/release-status` |
| Architecture | 1 container = API + SPA estática | Sem Node em runtime |
| Docs | PT-BR; autor/data em artefatos novos | CHANGELOG na entrega |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | Raiz: `Dockerfile`, `.dockerignore`, `docker-compose.yml`; `scripts/` (pack); opcional `releases/` gitignored | Código app em `src/`, `web/`, `config/`, `docs/kb/`, `database/serving_audit/` copiados na imagem |
| **KB Domains** | gifi-domain (template); paths de serving via `_index.yaml` | Não é feature de domínio de negócio |
| **IaC Impact** | **None** neste MVP | Contrato documentado para ciclo Azure futuro |
| **Config** | `config/serving.yaml` + env `GIFI_SERVING_*` no compose | Override host/port via CLI no entrypoint |
| **Guia operacional** | Atualizar `TAREFA_DOCKER_SERVING_PROD.md` e/ou seção no guia Azure | Comandos pack/build/smoke |

---

## Release Package Contract

> Contrato de artefatos (não schema tabular). Fonte: guia Azure §4 + tarefa Docker A1.

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| FS local pós-jobs | `models/`, `reports/`, pointers | ~25–40 MB | Por release `run_id` | DS / Eng GIFI |
| App + UI source | `src/`, `web/`, `config/`, KB, audit SQL | N/A | HEAD do repo | Dev |

### Manifesto mínimo (MUST no pack e no `COPY` da imagem)

| Família | Paths (relativos ao repo root na imagem) |
|---------|------------------------------------------|
| Cascata L3 | `models/candidates/<default_run_id>/` (joblibs + manifesto) |
| Pointer campeão | `models/candidates/current_champion.json` (se usado) |
| Aceite L4 | `reports/acceptance/<default_run_id>/acceptance_report.json` |
| Forecast | `models/primeira_base/` + `current_forecast.json` + joblib referenciado |
| What-if TSA | `current_tsa.json` + joblib referenciado sob `models/primeira_base/` |
| Imputer | `models/ingest/extrativo_serving_imputer.joblib` + pointer |
| Relatórios status | `reports/TSA_FORECAST_OPERACIONAL.json`, `reports/TSA_PRIMEIRA_BASE_MODELING.json` |
| Template + root | `docs/kb/_index.yaml`, `docs/kb/gifi-domain/specs/template_cenario_v0.yaml` |
| Audit schema | `database/serving_audit/001_init.sql` (via COPY do repo, não necessariamente no tarball ML) |
| Config | `config/serving.yaml` |

### Layout de saída do pack

| Item | Valor |
|------|-------|
| Diretório | `releases/{run_id}/` espelhando paths acima **ou** tarball `gifi-release-{run_id}.tar.gz` com a mesma árvore |
| Naming Blob (documentado) | `releases/{run_id}/` ou `gifi-release-{run_id}.tar.gz` — implementação de upload **fora** deste MVP |
| `run_id` | Deve alinhar a `default_run_id` / forecast / tsa da config de release usada no compose |

### Completeness

- Pack falha se qualquer path MUST do manifesto estiver ausente no FS fonte
- Smoke falha se status endpoints ≠ 200 após bake

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Existe no ambiente de build um FS local com artefatos de release válidos (champion + forecast + tsa + acceptance) | Pack falha até gerar release local via jobs | [x] Confirmado no brainstorm (samples b+c) |
| A-002 | CLI `serve run` aceita `--host` / `--port` e sobrescreve YAML | Precisaria wrapper shell ou mudança em config | [x] Validado: `src/serving/main.py` → `uvicorn.run(..., host=host or settings.host, port=port or settings.port)` |
| A-003 | SPA montada pelo FastAPI em `/` quando `web/dist` existe | Compose smoke de `/` falha | [x] Validado: `src/serving/app.py` monta `StaticFiles` em `/` se `cfg.static_path.is_dir()`; default `static_dir=web/dist` |
| A-004 | Healthcheck com `/api/release-status` é suficiente para compose (pode ser mais lento que `/healthz`) | Timeouts de health — ajustar interval/start_period | [x] Aceito conscientemente |
| A-005 | Stage Python instala deps a partir de `pyproject.toml` / lock exportável | Design escolhe **uma** das opções aceitas: (1) `uv export` → `requirements.txt` + pip, ou (2) `pip install .` / `uv sync` no build — ambas válidas | [x] Não bloqueia: duas alternativas equivalentes documentadas |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Dor clara: sem pacote/contrato reprodutível pré-Azure |
| Users | 3 | Eng GIFI/DS, Dev L5, TI (ciclo seguinte) com dores |
| Goals | 3 | MUST/SHOULD/COULD alinhados a A–C da tarefa |
| Success | 3 | Critérios numeráveis (HTTP 200, persistência volume, zero diff serving) |
| Scope | 3 | Limites explícitos; contrato `ReleaseStatusResponse` citado; NFRs de segurança deferidos com ponteiro |
| **Total** | **15/15** | Ready for Design |

---

## Open Questions

Nenhuma bloqueante. Itens de **Design** apenas:

1. Path de workdir no container (`/app` vs outro) e como `_find_repo_root` resolve com a árvore copiada.
2. Se `releases/{run_id}/` fica gitignored e o build usa `ARG RELEASE_DIR` / `COPY` seletivo.
3. Forma exata do export de deps (`uv export` vs `pip install` do `pyproject`) — A-005.

**None blocking — ready for Design.**

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-14 | Emerson Antônio / define-agent | Extraído do BRAINSTORM; ATs AT-DSP-001…009; Release Package Contract |
| 1.1 | 2026-07-14 | Emerson Antônio / define-agent | Pós-judge: schema `ReleaseStatusResponse` no AT-DSP-004; A-002/A-003 validados no código; NFR segurança explicitamente deferido; score 15/15 |
| 1.2 | 2026-07-14 | Emerson Antônio / define-agent | NFR-SEC packaging (sem segredos, localhost-only, USER não-root soft); AT-DSP-010/011; zero-diff serving explicitado; A-005 fechado com alternativas |
| 1.3 | 2026-07-14 | Emerson Antônio / ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_DOCKER_SERVING_PROD.md`
