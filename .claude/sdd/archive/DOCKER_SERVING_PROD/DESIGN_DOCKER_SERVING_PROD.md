# DESIGN: Docker Serving Prod (MVP container local)

> Empacotar release local → bake em imagem multi-stage → validar com compose (1 serviço + volume `logs`), sem alterar `src/serving`.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | DOCKER_SERVING_PROD |
| **Date** | 2026-07-14 |
| **Author** | Emerson Antônio |
| **DEFINE** | [DEFINE_DOCKER_SERVING_PROD.md](./DEFINE_DOCKER_SERVING_PROD.md) |
| **Status** | ✅ Shipped |
| **Judge** | 2026-07-14 advisory FAIL → mitigations em v1.1 (autoridade: DESIGN) |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  Host (dev)                                                                  │
│                                                                              │
│  models/ + reports/ (gitignored) ──▶ scripts/pack_serving_release.py         │
│         │                              │ fail-fast se path MUST ausente      │
│         │                              ▼                                     │
│         │                    releases/{run_id}/                              │
│         │                      ├── models/...                                │
│         │                      ├── reports/...                               │
│         │                      └── MANIFEST.json (checksum + lista)          │
│         │                              │                                     │
│         │         docker compose build (ARG RELEASE_RUN_ID)                  │
│         │                              ▼                                     │
│  ┌──────┴──────────────────────────────────────────────────────────────┐     │
│  │ Stage 1: node:20-bookworm  →  npm ci && npm run build → web/dist    │     │
│  │ Stage 2: python:3.12-slim  →  apt libgomp1 + pip install .          │     │
│  │   WORKDIR /app  (= repo root lógico)                                │     │
│  │   COPY src config docs/kb database/serving_audit pyproject.toml     │     │
│  │   COPY --from=node web/dist                                         │     │
│  │   COPY config/serving.docker.yaml → config/serving.yaml             │     │
│  │   COPY releases/{run_id}/models → /app/models                       │     │
│  │   COPY releases/{run_id}/reports → /app/reports                     │     │
│  │   USER gifi (soft) · CMD serve run --host 0.0.0.0 --port ${PORT}    │     │
│  └─────────────────────────────┬───────────────────────────────────────┘     │
│                                │ ports 127.0.0.1:8000:8000                   │
│                                ▼                                             │
│                    volume serving_audit → /app/logs                          │
│                    smoke: /api/release-status · forecast/status ·            │
│                           predict-tsa/status · GET /                         │
└─────────────────────────────────────────────────────────────────────────────┘

_find_repo_root: sobe a partir de CWD até achar docs/kb/_index.yaml
→ WORKDIR /app com essa árvore garante repo_root=/app sem patch em serving.
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `config/serving_release_manifest.yaml` | Lista canônica de globs/paths MUST do pacote | YAML |
| `scripts/pack_serving_release.py` | Copia FS → `releases/{run_id}/`; resolve pointers; fail-fast | Python 3.12 |
| `scripts/smoke_serving_docker.sh` | Curl asserts AT-DSP-004…006 | Bash |
| `Dockerfile` | Multi-stage Node→Python; bake artefatos | Docker |
| `.dockerignore` | Context enxuto; exclu segredos; não ignorar `releases/` | Docker |
| `docker-compose.yml` | 1 serviço + volume logs + healthcheck | Compose v2 |
| `config/serving.docker.yaml` | Overlay de config **dentro da imagem** (`demo_default: false`, run ids) | YAML |
| Docs | Runbook em `TAREFA_DOCKER_SERVING_PROD.md` + CHANGELOG | Markdown |
| Test unitário pack (COULD) | AT-DSP-001/002 com tmp_path | pytest |

**Inalterado:** `src/serving/**`, `web/src/**` (só build Vite no stage Node).

---

## Key Decisions

### Decision 1: WORKDIR `/app` = repo root lógico

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** `_find_repo_root` em `src/serving/config.py` procura `docs/kb/_index.yaml` a partir do CWD.

**Choice:** `WORKDIR /app`; copiar a árvore mínima de modo que `/app/docs/kb/_index.yaml` exista; processo inicia com CWD `/app`.

**Rationale:** Zero mudança em serving; paths relativos de YAML/`models/`/`web/dist` resolvem iguais ao monorepo.

**Alternatives Rejected:**
1. `PYTHONPATH` + layout diferente — risco de root detect falhar.
2. Env `GIFI_SERVING_REPO_ROOT` — exigiria patch em `ServingSettings` (fora do MVP).

**Consequences:**
- Imagem não precisa do `.git`.
- KB mínima + template devem estar na imagem (já no manifesto DEFINE).

---

### Decision 2: Artefatos via `releases/{run_id}/` + `ARG RELEASE_RUN_ID` (não bake de `/models` solto)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** DEFINE exige pack versionável alinhado a Blob futuro; `/models` no working tree é sujo.

**Choice:**
- Pack produz `releases/{run_id}/{models,reports}/...` espelhando paths de runtime.
- `.gitignore` adiciona `/releases/`.
- Build: `docker compose build --build-arg RELEASE_RUN_ID=<id>`; Dockerfile `COPY releases/${RELEASE_RUN_ID}/models /app/models` e idem `reports`.
- Default compose: variável `.env.docker` ou `RELEASE_RUN_ID` no compose (não o `.env` de secrets).

**Rationale:** Contrato Blob `releases/{run_id}/` já documentado; build falha cedo se pasta ausente.

**Alternatives Rejected:**
1. COPY direto de `./models` — rejeitado no brainstorm.
2. Download Blob no build — fora do MVP.

**Consequences:**
- Pré-requisito: rodar pack antes do build.
- Context Docker inclui só a release pedida (não todas as pastas em `releases/`).

---

### Decision 3: Overlay `config/serving.docker.yaml` → `config/serving.yaml` na imagem

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** `ServingSettings.from_yaml()` faz `cls(**data_do_yaml)`. Em pydantic-settings v2, **init kwargs prevalecem sobre env** — portanto `GIFI_SERVING_DEMO_DEFAULT=false` no compose **não sobrescreve** `demo_default: true` do YAML local.

**Choice:** Manter `config/serving.yaml` de desenvolvimento intacto no Git. Commitar `config/serving.docker.yaml` com:
- `demo_default: false`
- `host: "0.0.0.0"` (redundante com CLI; documentação)
- `default_run_id` / `default_forecast_run_id` / `default_tsa_run_id` alinhados à release de smoke documentada (comentário: atualizar quando trocar pack)
- `cors_origins: []` (same-origin via SPA no mesmo host)
- demais campos iguais ao YAML local (`audit_*`, paths)

Dockerfile: `COPY config/serving.docker.yaml /app/config/serving.yaml` **depois** de copiar `config/` (ou copiar config sem serving.yaml e só o docker overlay).

**Rationale:** Atende AT-DSP-004 sem tocar `src/serving`; env no compose fica opcional/documental.

**Alternatives Rejected:**
1. Patch em `from_yaml` para preferir env — viola zero-diff serving.
2. Sed no entrypoint — frágil e opaco.

**Consequences:**
- Troca de `run_id` de release: atualizar `serving.docker.yaml` **e** pack (passo no runbook).
- Compose ainda passa `PORT` via CLI/`environment`.

---

### Decision 4: Dependências Python = `pip install .` no stage runtime

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** A-005 permitia `uv export` ou install do `pyproject`.

**Choice:** No stage Python: copiar `pyproject.toml` + `README.md` (setuptools) + `src/`; `pip install --no-cache-dir .` (sem extras `dev`). Instalar `libgomp1` (e deps build se wheel falhar: `build-essential` só se necessário — preferir wheels manylinux).

**Rationale:** Um passo, alinhado ao packaging setuptools já usado (`[project.scripts] serve=...`); sem commitar `requirements.txt` gerado.

**Alternatives Rejected:**
1. `uv export` + requirements commitado — arquivo extra para manter.
2. Copiar `.venv` host — não portável.

**Consequences:**
- Builds reproduzem a resolução pip do momento (aceito no MVP); Marco CI pode pin-lock depois.

---

### Decision 5: Bind compose em `127.0.0.1:8000` + USER não-root soft

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** NFR-SEC-02/03.

**Choice:**
- `ports: ["127.0.0.1:8000:8000"]` (não `0.0.0.0` no host).
- Dockerfile cria user `gifi` (uid 10001); `chown -R gifi:gifi /app`; `USER gifi`.
- Diretório `/app/logs` com permissão de escrita; volume nomeado monta aí.
- Entrypoint opcional: `mkdir -p /app/logs` antes do serve (se USER gifi, logs deve ser writable no image layer).

**Rationale:** Localhost-only no host; app ainda escuta `0.0.0.0` **dentro** do container (AT-DSP-008).

**Invariants de exposição (resposta ao judge):**
- **Dentro do container**, bind `0.0.0.0` é **obrigatório** para o contrato Azure App Service e para `ports:` do Compose. Escutar só `127.0.0.1` *inside* quebra o mapeamento de porta.
- **Fronteira de segurança do MVP** = publish do host em `127.0.0.1:8000` + runbook (nunca `-p 8000:8000` sem bind de loopback). Misconfiguration do publish é risco operacional mitigado por compose canônico + docs — não por mudar o bind interno.
- **Réplicas:** scale/replicas **proibido** neste compose (SQLite + volume compartilhado). `deploy.replicas` implícito = 1 até migrar audit (fora MVP).

**Alternatives Rejected:**
1. Root no container — pior default.
2. Auth na app — fase E.
3. Bind `127.0.0.1` dentro do container — rejeitado: incompatível com App Service e port publish.

**Consequences:**
- Smoke e TI usam o mesmo entrypoint cloud-friendly.
- Quem alterar o compose para publish aberto assume risco documentado (fase E ainda obrigatória antes de exposição).

---

### Decision 6: Pack em Python com manifesto YAML

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-14 |

**Context:** Pointers JSON (`current_forecast.json`, etc.) apontam joblibs relativos; shell puro erra fácil.

**Choice:** `scripts/pack_serving_release.py`:
1. Lê `config/serving_release_manifest.yaml` (paths MUST + regras de pointer).
2. Resolve `run_id` L4 (arg `--run-id` ou default de `config/serving.yaml` / `--from-serving-yaml`).
3. Copia árvores e arquivos referenciados pelos pointers.
4. Escreve `releases/{run_id}/MANIFEST.json` (lista + tamanho + sha256 opcional).
5. Exit 2 se faltou MUST (mensagem lista paths).

**Rationale:** Mesma linguagem do repo; testável com pytest.

**Alternatives Rejected:**
1. Só bash — frágil para JSON pointers.
2. Tarball sem árvore expandida — Docker COPY de tree é mais simples no MVP (`--tarball` COULD depois).

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `config/serving_release_manifest.yaml` | Create | Paths MUST + pointer rules | (general) | None |
| 2 | `config/serving.docker.yaml` | Create | Overlay config bake na imagem | (general) | `config/serving.yaml` (base) |
| 3 | `scripts/pack_serving_release.py` | Create | Pack FS → `releases/{run_id}/` | @python-developer | 1 |
| 4 | `scripts/smoke_serving_docker.sh` | Create | Smoke AT-DSP-004…006 | @shell-script-specialist | compose up |
| 5 | `Dockerfile` | Create | Multi-stage bake | @shell-script-specialist / (general) | 2, pack |
| 6 | `.dockerignore` | Create | Context seguro/enxuto | (general) | None |
| 7 | `docker-compose.yml` | Create | 1 serviço + volume + healthcheck | (general) | 5 |
| 8 | `.gitignore` | Modify | Adicionar `/releases/` | (general) | None |
| 9 | `docs/guides/TAREFA_DOCKER_SERVING_PROD.md` | Modify | Runbook pack→build→smoke; marcar A–C; Blob naming | (general) | 3–7 |
| 10 | `docs/guides/AZURE_APP_SERVICE_REQUISITOS.md` | Modify | Nota “Dockerfile existe; MVP local” + link tarefa | (general) | 5 |
| 11 | `docs/CHANGELOG.md` | Modify | Entrada entrega Build | (general) | — |
| 12 | `tests/scripts/test_pack_serving_release.py` | Create (COULD→SHOULD se tempo) | AT-DSP-001/002 | @test-generator | 3 |

**Total Files:** 11 MUST + 1 COULD  
**Proibido neste Build:** qualquer arquivo sob `src/serving/`

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @python-developer | 3, (12) | Script de pack com paths/pointers tipados |
| @shell-script-specialist | 4, 5 | Smoke bash; revisão Dockerfile/entrypoint |
| @test-generator | 12 | Pytest do pack fail-fast |
| (general) | 1, 2, 6, 7, 8, 9, 10, 11 | YAML/compose/docs de packaging |

---

## Code Patterns

### Pattern 1: Pack fail-fast

```python
# scripts/pack_serving_release.py (esqueleto)
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml


def pack(repo_root: Path, run_id: str, manifest_path: Path) -> Path:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    dest = repo_root / "releases" / run_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    missing: list[str] = []
    copied: list[str] = []

    for rel in manifest["must_paths"]:
        # permite {run_id} no glob
        pattern = rel.replace("{run_id}", run_id)
        src = repo_root / pattern
        if not src.exists():
            missing.append(pattern)
            continue
        target = dest / pattern
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
        copied.append(pattern)

    # pointer rules: carregar JSON e copiar artifact_path referenciado
    for rule in manifest.get("pointer_rules", []):
        pointer = repo_root / rule["pointer"].replace("{run_id}", run_id)
        if not pointer.exists():
            missing.append(str(rule["pointer"]))
            continue
        data = json.loads(pointer.read_text(encoding="utf-8"))
        # copiar o pointer para dest
        ...
        art = data.get(rule.get("artifact_key", "artifact_path"))
        if art:
            art_path = (repo_root / art).resolve()
            if not art_path.exists():
                missing.append(art)
            else:
                rel_art = art_path.relative_to(repo_root)
                ...

    if missing:
        print("ERRO: paths ausentes no pack:", *missing, sep="\n  - ", file=sys.stderr)
        raise SystemExit(2)

    (dest / "MANIFEST.json").write_text(
        json.dumps({"run_id": run_id, "paths": copied}, indent=2),
        encoding="utf-8",
    )
    return dest
```

### Pattern 2: Dockerfile multi-stage (contrato)

```dockerfile
# Dockerfile — referência de Build (ajustar pins se necessário)
# syntax=docker/dockerfile:1

ARG RELEASE_RUN_ID
FROM node:20-bookworm-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ARG RELEASE_RUN_ID
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin gifi

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY config ./config
COPY config/serving.docker.yaml ./config/serving.yaml
COPY docs/kb ./docs/kb
COPY database/serving_audit ./database/serving_audit
COPY --from=web /web/dist ./web/dist

# Bake da release (pré-req: scripts/pack_serving_release.py)
COPY releases/${RELEASE_RUN_ID}/models ./models
COPY releases/${RELEASE_RUN_ID}/reports ./reports

RUN mkdir -p /app/logs && chown -R gifi:gifi /app
USER gifi
EXPOSE 8000
CMD ["sh", "-c", "serve run --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Pattern 3: docker-compose.yml

```yaml
# Autor: Emerson Antônio — 2026-07-14
services:
  serving:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        RELEASE_RUN_ID: ${RELEASE_RUN_ID:?Defina RELEASE_RUN_ID (saída do pack)}
    image: gifi-serving:local
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      PORT: "8000"
    volumes:
      - serving_audit:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/release-status')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: "no"

volumes:
  serving_audit:
```

### Pattern 4: Manifest YAML (esqueleto)

```yaml
# config/serving_release_manifest.yaml
# Autor: Emerson Antônio — 2026-07-14
must_paths:
  - "models/candidates/{run_id}"
  - "models/candidates/current_champion.json"
  - "reports/acceptance/{run_id}/acceptance_report.json"
  - "models/primeira_base/current_forecast.json"
  - "models/primeira_base/current_tsa.json"
  - "models/ingest/extrativo_serving_imputer.joblib"
  - "reports/TSA_FORECAST_OPERACIONAL.json"
  - "reports/TSA_PRIMEIRA_BASE_MODELING.json"

pointer_rules:
  - pointer: "models/primeira_base/current_forecast.json"
    artifact_key: "artifact_path"
  - pointer: "models/primeira_base/current_tsa.json"
    artifact_key: "artifact_path"
  - pointer: "models/candidates/current_champion.json"
    # se pointer listar paths de joblib, copiar família referenciada
    artifact_key: "artifact_path"
  - pointer: "models/ingest/current_extrativo_imputer.json"  # se existir; senão só joblib MUST
    optional: true
    artifact_key: "artifact_path"

# Nota Build: se current_champion não tiver artifact_path único,
# copiar árvore models/candidates/{run_id} já cobre joblibs do simulado.
```

### Pattern 5: serving.docker.yaml (campos críticos)

```yaml
# config/serving.docker.yaml — bake na imagem (não usar em dev local)
host: "0.0.0.0"
port: 8000
default_run_id: "REPLACE_WITH_PACKED_RUN_ID"
default_forecast_run_id: "REPLACE_WITH_FORECAST_RUN_ID"
default_tsa_run_id: "REPLACE_WITH_TSA_RUN_ID"
forecast_models_root: "models/primeira_base"
reports_root: "reports/acceptance"
static_dir: "web/dist"
template_path: "docs/kb/gifi-domain/specs/template_cenario_v0.yaml"
cors_origins: []
demo_default: false
ephemeral_prefix: "ui-"
audit_enabled: true
audit_db_path: "logs/serving_audit.db"
audit_max_body_bytes: 65536
```

---

## Data Flow

```text
1. DS termina accept → FS com models/ + reports/acceptance/{run_id}
   │
   ▼
2. python scripts/pack_serving_release.py --run-id <L4_RUN_ID>
   │  valida manifesto · copia · MANIFEST.json
   ▼
3. Atualizar config/serving.docker.yaml (run ids) se mudaram
   │
   ▼
4. RELEASE_RUN_ID=<id> docker compose build
   │  Node build SPA · pip install · COPY bake
   ▼
5. docker compose up -d
   │  volume logs · healthcheck release-status
   ▼
6. scripts/smoke_serving_docker.sh
   │  asserts JSON ReleaseStatusResponse + status forecast/tsa + SPA
   ▼
7. (ciclo Azure futuro) upload releases/{id} → Blob · mesma Dockerfile no CI
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|------------------|----------------|
| Filesystem local (`models/`, `reports/`) | Leitura pack | N/A |
| Docker Engine | Build/run local | N/A (daemon local) |
| Azure Blob / ACR / App Service | **Documentado only** | Fora MVP |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Pack missing path → exit 2; pack happy tmp tree | `tests/scripts/test_pack_serving_release.py` | pytest | AT-DSP-001/002 |
| Manual / script | Compose build+up+smoke | `scripts/smoke_serving_docker.sh` | curl + jq | AT-DSP-003…008, 010–011 |
| Gate processo | Diff serving | `git diff --name-only -- src/serving/` | git | AT-DSP-009 |

Smoke JSON mínimo (`release-status`):

```bash
test "$(jq -r '.release_ok' out.json)" = "true"
test "$(jq -r '.demo_mode' out.json)" = "false"
test "$(jq -r '.run_id' out.json)" = "$EXPECTED_RUN_ID"
```

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| Path MUST ausente no pack | Exit 2 + lista path | No — gerar artefatos via jobs |
| `RELEASE_RUN_ID` não definido | Compose falha na interpolação `:?` | No |
| Pasta `releases/{id}` ausente no build | Docker COPY falha | No — rodar pack |
| Healthcheck timeout (cold start) | `start_period: 60s`; aumentar se necessário | Soft retry do healthcheck |
| SPA 404 | Verificar stage Node e `web/dist` no /app | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `RELEASE_RUN_ID` | env (host) | (obrigatório) | Pasta sob `releases/` bakeada |
| `PORT` | env (container) | `8000` | Porta Uvicorn / App Service |
| `config/serving.docker.yaml` | file (imagem) | — | demo_default false + run ids |
| `config/serving_release_manifest.yaml` | file (host) | — | Contrato de pack |
| Bind host publish | compose | `127.0.0.1:8000` | NFR-SEC-02 |

---

## Security Considerations

- `.dockerignore` **MUST** excluir: `.env`, `.env.*`, `**/*.pem`, `**/*credential*`, `.venv`, `web/node_modules`, `.git`, `tests/`, notebooks, Excel brutos — **não** excluir `releases/`.
- Publish só em localhost; runbook alerta contra `-p 8000:8000` aberto.
- USER `gifi` (soft); se volume permissions falharem em Docker Desktop, documentar workaround sem voltar a root como default.
- Auth / path hardening = fase E (`SECURITY_SERVING_DEBITOS.md`).
- **Segredos neste MVP:** a imagem **não** consome connection strings nem API keys. Audit = SQLite local no volume. Key Vault / Managed Identity entram no ciclo Azure (fora deste DESIGN). Não inventar Docker secrets vazios.

---

## Failure / Rollback (MVP local)

| Cenário | Ação |
|---------|------|
| Build falhou | Corrigir pack/`RELEASE_RUN_ID`; `docker compose build` de novo (sem estado destruído no host além de layers intermediárias) |
| Container unhealthy / smoke falha | `docker compose logs serving`; `docker compose down`; inspecionar pack + `serving.docker.yaml`; não é “deploy prod” |
| Rollback de imagem | Manter tag anterior opcional: `docker tag gifi-serving:local gifi-serving:prev` antes do rebuild; `docker compose down` + `image: gifi-serving:prev` se necessário |
| Volume audit corrompido | `docker compose down`; `docker volume rm <project>_serving_audit` (perda de audit local aceitável em dev) |

**Fora MVP:** slot swap App Service, ACR retention, rollback automatizado de pipeline.

---

## Concurrency / shared volume

- Compose **single replica** apenas. Comment no `docker-compose.yml`: `# do not scale — SQLite audit`.
- Múltiplas instâncias no mesmo volume SQLite = **indefinido / proibido** (já no DEFINE Out of Scope). Judge medium “concurrency” = mitigado por constraint, não por locks distribuídos.

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | stdout/stderr Uvicorn (Compose logs) |
| Audit | SQLite em volume `/app/logs` — já existente no serving |
| Health | Compose healthcheck → `/api/release-status` |
| Metrics/Tracing | Fora MVP |

---

## Runbook (texto-alvo no guia)

```text
# 1) Pack (artefatos locais válidos)
python scripts/pack_serving_release.py --run-id <L4_RUN_ID>

# 2) Alinhar config/serving.docker.yaml (run ids) se necessário

# 3) Build + up (somente localhost)
export RELEASE_RUN_ID=<L4_RUN_ID>
docker compose up --build -d

# 4) Smoke
./scripts/smoke_serving_docker.sh

# 5) Down
docker compose down
# volume serving_audit persiste até docker volume rm …

AVISO: não publicar esta imagem/porta em rede corporativa ou internet
até autenticação (fase E). Uso restrito a http://127.0.0.1:8000
```

Blob (documentar, não implementar): `gifi-release-{run_id}.tar.gz` ou prefixo `releases/{run_id}/` no Storage Account — CI futuro baixa no `docker build`.

---

## Build Sequence (ordem recomendada)

1. Manifest YAML + `serving.docker.yaml` + `.gitignore` `/releases/`
2. `pack_serving_release.py` (+ teste unitário se COULD)
3. `.dockerignore` + `Dockerfile`
4. `docker-compose.yml`
5. `smoke_serving_docker.sh`
6. Docs tarefa + guia Azure + CHANGELOG
7. Gate: `git diff --name-only -- src/serving/` vazio
8. Smoke real com artefatos locais do autor

---

## Open Questions resolvidas (DEFINE → DESIGN)

| # | Pergunta DEFINE | Resolução |
|---|-----------------|-----------|
| 1 | Workdir / `_find_repo_root` | `/app` com `docs/kb/_index.yaml` |
| 2 | `releases/` + ARG | Sim; gitignore; `RELEASE_RUN_ID` |
| 3 | Deps | `pip install .` no stage Python |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-14 | Emerson Antônio / design-agent | Arquitetura pack→bake→compose; decisões WORKDIR, overlay YAML (env não sobrescreve), pip install, localhost bind |
| 1.1 | 2026-07-14 | Emerson Antônio / design-agent | Pós-judge: invariants 0.0.0.0-in/127.0.0.1-host; rollback local; sem secrets no MVP; réplica única no volume |
| 1.2 | 2026-07-14 | Emerson Antônio / ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_DOCKER_SERVING_PROD.md`
