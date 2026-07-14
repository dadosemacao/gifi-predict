# Requisitos Azure — Serving + UI (Produção)

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.0  
**Status:** Levantamento de requisitos (sem implementação)  
**Escopo:** Camada 5 (FastAPI serving + SPA React) em **Azure App Service (Linux container)** — ambiente **Produção**.  
**Fora de escopo:** ingest batch, treino, acceptance gate como jobs cloud; Dev/HML.

---

## 1. Objetivo

Listar o que é **necessário e suficiente** para publicar a aplicação GIFI Predict (API + UI) em Produção no Azure App Service, com base no estado atual do código (`src/serving/`, `web/`, `config/serving.yaml`) e nos débitos já registrados.

Premissa de produto: um único Web App serve **API REST** e a **SPA** estática (`web/dist` montado em `/` pelo FastAPI).

---

## 2. Arquitetura alvo (resumo)

```text
Cliente (rede corporativa / Private Link)
        │ HTTPS
        ▼
Azure App Service (Linux + container)
  ├── Uvicorn + FastAPI  (serving)
  ├── SPA React          (web/dist)
  ├── Artefatos ML       (models/* + reports/*)  ← bake na imagem ou mount
  └── Audit SQLite       (logs/serving_audit.db) ← storage persistente
        │
        ├── Azure Container Registry (imagem)
        ├── Azure Files / Blob       (modelos + audit)
        ├── Key Vault                (segredos)
        ├── Application Insights     (telemetria)
        └── VNet + Private Endpoint  (isolamento)
```

Não há `Dockerfile` no repositório hoje — packaging container é **pré-requisito de implementação**.

---

## 3. Stack de runtime (obrigatório)

| Item | Requisito | Fonte |
|------|-----------|-------|
| Python | **3.12** (recomendado); ≥3.11 aceito | `.python-version`, `pyproject.toml` |
| App server | Uvicorn + FastAPI | `serve run` → `serving.main` |
| Bind | `0.0.0.0` e porta do App Service (`PORT` / `WEBSITES_PORT`) | Hoje: `host: 127.0.0.1` em `config/serving.yaml` — **incompatível com cloud sem override** |
| Frontend | Build estático Vite → `web/dist` | `cd web && npm run build` (Node 18+) |
| Detecção de root | Presença de `docs/kb/_index.yaml` no filesystem do container | `serving.config._find_repo_root` |
| Dependências nativas | OpenMP / libs para `lightgbm`, `xgboost`, `catboost`, `scikit-learn` | `pyproject.toml` |

Comando de entrada esperado (proposta):

```bash
serve run --host 0.0.0.0 --port ${PORT:-8000}
```

---

## 4. Artefatos que precisam existir no runtime

Sem estes paths, endpoints retornam 404/503.

| Família | Paths mínimos | Tamanho aprox. (estado local) | Usado por |
|---------|---------------|-------------------------------|-----------|
| Cascata L3 | `models/candidates/<default_run_id>/*.joblib` + manifesto | ~15 MB (champion atual) | `POST /api/simulate` |
| Pointer campeão | `models/candidates/current_champion.json` (se caminho champion) | KB | fallback champion |
| Aceite L4 | `reports/acceptance/<default_run_id>/acceptance_report.json` | <1 MB | `/api/release-status`, gate `demo=false` |
| Forecast | `models/primeira_base/` + `current_forecast.json` + joblib | ~4–10 MB | `/api/forecast` |
| What-if TSA | `models/primeira_base/` + `current_tsa.json` + joblib | <1 MB (Lasso) | `/api/predict-tsa` |
| Imputer Extrativo | `models/ingest/extrativo_serving_imputer.joblib` + pointer | ~5 MB | Tier B forecast/tsa |
| Relatórios status | `reports/TSA_FORECAST_OPERACIONAL.json`, `reports/TSA_PRIMEIRA_BASE_MODELING.json` | <1 MB | endpoints `/status` |
| Template | `docs/kb/gifi-domain/specs/template_cenario_v0.yaml` | pequeno | `GET /api/template` |
| SPA | `web/dist/**` | ~0.7 MB | UI |
| Audit schema | `database/serving_audit/001_init.sql` | pequeno | bootstrap SQLite |
| Config | `config/serving.yaml` (+ YAML de simulação se o serviço de simulate carregar settings L3) | pequeno | settings |

**Pacote mínimo estimado para Produção (só o que a API lê):** da ordem de **~25–40 MB** de artefatos ML + reports, mais a imagem Python.

> Modelos e `reports/` estão tipicamente fora do Git (`gitignored`). O pipeline de deploy **deve** versionar e anexar o pacote de artefatos (Blob/ACR layer/Azure Files).

---

## 5. Recursos Azure (SKU / serviços)

### 5.1 Obrigatórios

| Recurso | Função | Notas de sizing inicial |
|---------|--------|-------------------------|
| Resource Group | Contêiner lógico | 1 RG prod |
| App Service Plan (Linux) | Compute | **≥ 2 vCPU / 3.5 GB RAM** (ex.: P1v3 ou B2 com validação de carga). Inferência sklearn/boosting + CatBoost/XGBoost é CPU-bound |
| App Service (Web App) | Host do container | Runtime: **custom container** |
| Azure Container Registry | Imagens | Premium se Private Link for exigido |
| Storage Account | Persistência | **Azure Files** para `logs/` (SQLite) e opcionalmente `models/`; Blob para histórico de releases |
| Key Vault | Segredos (API key, connection strings) | Acesso via Managed Identity |
| Log Analytics + Application Insights | Logs / métricas / falhas | Correlacionar latência de `/api/simulate` e `/api/forecast` |
| Managed Identity | Auth recurso→recurso | Sem secrets no App Settings quando possível |

### 5.2 Rede e exposição (Produção)

| Recurso | Requisito |
|---------|-----------|
| VNet + subnet App Service | Integração VNet (outbound) |
| Private Endpoint do Web App | Preferível: **sem IP público**; acesso só via corporativo / VPN / ExpressRoute |
| Private DNS Zone | Resolução do hostname privado |
| NSG / firewall corporativo | Restringir origem |
| TLS | HTTPS only; certificado gerenciado ou custom |
| WAF (opcional mas recomendado) | Application Gateway ou Front Door se houver exposição controlada à internet |

### 5.3 Opcionais / evolutivos

| Recurso | Quando |
|---------|--------|
| Azure Front Door / App Gateway | Multi-região, WAF, rate limit na borda |
| Azure Cache for Redis | Só se rate-limit/sessão forem além do in-process |
| Azure SQL / PostgreSQL | Se migrar audit SQLite → DB gerenciado (não obrigatório no MVP cloud) |
| Azure Monitor alerts | 5xx, latência p95, disponibilidade |

---

## 6. Configuração de runtime

### 6.1 Settings que devem mudar em Produção

Fonte: `config/serving.yaml` + env `GIFI_SERVING_*` (`ServingSettings`).

| Chave | Local atual | Valor prod esperado |
|-------|-------------|---------------------|
| `host` | `127.0.0.1` | `0.0.0.0` (CLI ou override) |
| `port` | `8000` | Porta do App Service |
| `cors_origins` | Vite localhost | Origens oficiais do hostname prod (ou lista vazia se same-origin) |
| `demo_default` | `true` | **`false`** (bind produtivo sob gate L4) |
| `default_run_id` | run de aceite | Run champion publicado |
| `default_forecast_run_id` / `default_tsa_run_id` | runs locais | Runs versionados no pacote de artefatos |
| `audit_enabled` | `true` | `true` |
| `audit_db_path` | `logs/serving_audit.db` | Path em volume persistente (Azure Files) |

App Settings típicos do App Service:

- `WEBSITES_PORT` / `PORT`
- `GIFI_SERVING_DEMO_DEFAULT=false`
- `GIFI_SERVING_HOST=0.0.0.0`
- `GIFI_SERVING_CORS_ORIGINS` (se serializado; hoje lista via YAML — alinhar implementação)
- Identity / Key Vault references para segredo de API key (quando implementado)

### 6.2 Health checks

Expor checagens estáveis para o App Service:

| Probe | Sugestão |
|-------|----------|
| Liveness | `GET /api/release-status` ou endpoint dedicado `/healthz` (**ainda não existe**) |
| Readiness | Confirmar presence de `acceptance_report.json` + pointers de modelo |

Gap: criar `/healthz` leve (sem carregar joblib) antes do go-live.

---

## 7. Persistência e estado

| Dado | Natureza | Risco no App Service | Requisitos |
|------|----------|----------------------|------------|
| `logs/serving_audit.db` | Mutable (SQLite WAL) | Disco local do container é **efêmero** (recycle perde dados) | Mount **Azure Files** em `/home/.../logs` ou path configurável; ou migrar audit para DB gerenciado |
| `models/*`, `reports/*` | Quase imutável por release | Podem ir na imagem **ou** no File Share | Preferir Blob + sync na deploy OU layer de artefatos versionada |
| Uploads multipart | Ephemeral | Memória/disco temp | Limite de tamanho (débito de segurança) |

Single instance: SQLite em File Share funciona com **uma** réplica. Scale-out horizontal exige migrar audit para store compartilhado seguro (SQL/Postgres) — **não previsto neste levantamento sem mudança de código**.

---

## 8. Segurança — blockers de go-live

Registro vigente: [`SECURITY_SERVING_DEBITOS.md`](SECURITY_SERVING_DEBITOS.md).

| Severidade | Item | Impacto Azure Prod |
|------------|------|--------------------|
| Critical | Sem autenticação / autorização / rate limit | **Bloqueia** exposição até mesmo em rede interna ampla |
| Critical | `joblib.load` sem contenção forte de path | Risco de desserialização se path for manipulável |
| High | Path traversal via `run_id` | Leitura fora de `models/` / `reports/` |
| High | Upload sem limite de tamanho | DoS / OOM no App Service |
| High | Handlers async com trabalho sync pesado | Latência e timeout sob concorrência |

### Controles Azure + aplicação (mínimo sugerido)

1. Rede privada (Private Endpoint) — reduzir superfície.
2. Autenticação na aplicação **ou** no App Service Authentication (Easy Auth / Entra ID) + API key para integração machine-to-machine.
3. Remediação dos débitos Critical/High no código antes de `demo_default: false` em tráfego real.
4. Managed Identity + Key Vault; nenhum segredo em plain text no repositório.
5. TLS obrigatório; HSTS na borda.
6. Desabilitar FTP/SCM público; restringir Kudu.
7. Scanner de imagem (Defender for Cloud / ACR scanning).

---

## 9. Empacotamento e CI/CD

### 9.1 Lacunas atuais

- Sem `Dockerfile` / compose.
- Sem pipeline CI (débito Marco 2 em `DEV_ENVIRONMENT.md`).
- Artefatos ML não versionados no Git.

### 9.2 Pipeline mínimo (Produção)

1. Build frontend (`web` → `dist`).
2. Export deps (`uv export` / `requirements.txt`).
3. Copiar pacote de artefatos release (models + reports + template KB necessário).
4. Build multi-stage image → push ACR.
5. Deploy slot do App Service (recomendado: slot `staging` → swap — mesmo com escopo “só prod”, slot reduz downtime).
6. Smoke: `/api/release-status`, `/api/forecast/status`, `/api/predict-tsa/status`, carga da SPA.
7. Tag de release alinhada ao `run_id` L4.

Ferramenta: Azure DevOps ou GitHub Actions (a definir pela TI Veracel).

---

## 10. Capacidade e desempenho

| Aspecto | Estimativa / requisito |
|---------|------------------------|
| Concorrência | Baixa/moderada (uso interno planejamento). Com handlers sync, 1–2 workers Uvicorn e App Service ≥2 vCPU |
| Timeout | Ajustar `requestTimeout` do App Service / proxies; `/api/simulate` e forecast podem levar segundos |
| Memória | Carregar pipelines joblib (RF/CatBoost/ET) → planejar **≥ 2–4 GB** headroom |
| Disco | File Share ≥ 5 GB inicial (audit + artifacts + logs) |
| Autoscaling | Só após audit deixar SQLite local; caso contrário **instância única** |

---

## 11. Observabilidade

| Capacidade | Requisito |
|------------|-----------|
| Logs stdout/stderr | Coletados pelo App Service → Log Analytics |
| Audit de negócio | SQLite persistente + retenção (política TI) |
| Métricas | Availability test interno; alertas 5xx e p95 |
| Tracing | OpenTelemetry → Application Insights (evolutivo; não shipped) |

---

## 12. Checklist de prontidão (Produção)

### Infra Azure

- [ ] RG, Plan, Web App (container), ACR, Storage, Key Vault, Insights
- [ ] VNet + Private Endpoint + DNS
- [ ] Managed Identity com RBAC mínimo (AcrPull, Key Vault Secrets User, Storage File/Blob)
- [ ] TLS e hostname corporativo
- [ ] Azure Files montado para audit (e opcionalmente models)

### Aplicação

- [ ] `Dockerfile` + entrypoint com `0.0.0.0` / `$PORT`
- [ ] Imagem contém `docs/kb/_index.yaml` + `web/dist` + artefatos do release
- [ ] `demo_default: false` e `release_ok: true` no report publicado
- [ ] CORS ajustado (same-origin preferível)
- [ ] `/healthz` (a implementar)
- [ ] Débitos Critical/High de segurança endereçados ou aceitos formalmente com mitigação de rede

### Operação

- [ ] Runbook de troca de modelo (`run_id` + artifacts)
- [ ] Backup/retenção do audit DB
- [ ] Smoke pós-deploy documentado
- [ ] Contato on-call / canal de incidente

---

## 13. Estimativa de entregáveis de implementação (próximos passos)

Ordem sugerida após este levantamento:

1. Remediação segurança mínima + `/healthz` + bind cloud-friendly.
2. `Dockerfile` multi-stage (Node build → Python runtime).
3. IaC (Bicep/Terraform) App Service + ACR + Files + Key Vault + rede.
4. Pipeline CI/CD com pacote de artefatos versionado.
5. Homologação de carga e decisão de SKU definitivo.

---

## 14. Referências

- [`DEV_ENVIRONMENT.md`](DEV_ENVIRONMENT.md) — runtime local e débitos CI
- [`SECURITY_SERVING_DEBITOS.md`](SECURITY_SERVING_DEBITOS.md) — blockers de segurança
- [`../api/README.md`](../api/README.md) — catálogo REST
- `config/serving.yaml` — defaults atuais
- `src/serving/config.py` — prefixo `GIFI_SERVING_*`
- PRD § integrações Azure/Databricks — fora do MVP de dados online; este doc cobre **hosting** da Camada 5

---

*Documento vivo. Atualizar quando houver Dockerfile, IaC ou decisão de SKU/rede pela TI Veracel.*
