# GIFI Ingest Knowledge Base

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.2

> **Purpose**: Padrões do Ingest Engine (I1–I5): dual-path, sinais, remediação, publicação versionada  
> **Confidence**: 0.95 (fonte: plano oficial do engine)  
> **Validated**: 2026-07-09  
> **Fontes**: `docs/sketch/ingest-engine.md`, `docs/sketch/analytical-backbone.md`, `docs/kb/gifi-domain/`

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/component-map.md](concepts/component-map.md) | I1–I5 e dependências |
| [concepts/signal-catalog.md](concepts/signal-catalog.md) | Códigos INGEST_* / ACCEPT_* |
| [concepts/artifact-contract.md](concepts/artifact-contract.md) | PK, semver, flags, fallback |
| [concepts/feature-column-contract.md](concepts/feature-column-contract.md) | Lista fixa negócio → canônico |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/dual-path-execution.md](patterns/dual-path-execution.md) | Batch histórico vs online cenário |
| [patterns/remediation-cycle.md](patterns/remediation-cycle.md) | Detectar→publicar→registrar |
| [patterns/warning-admissibility.md](patterns/warning-admissibility.md) | Matriz treino/holdout/inferência |

### Specs

| File | Purpose |
|------|---------|
| [specs/signal-catalog.yaml](specs/signal-catalog.yaml) | Catálogo machine-readable |
| [specs/artifact-contract.yaml](specs/artifact-contract.yaml) | Contrato dos artefatos L2 |
| [specs/warning-matrix.yaml](specs/warning-matrix.yaml) | Admissibilidade por contexto |
| [specs/feature-columns.yaml](specs/feature-columns.yaml) | Colunas fixas + tipos + unidades |

---

## Quick Reference

- [quick-reference.md](quick-reference.md)

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| `gifi-ingest-engineer` | All | Dono I1–I5 |
| `data-contracts-engineer` | artifact-contract* | ODCS |
| `data-quality-analyst` | signal-catalog, warning-* | Gates |
| `medallion-architect` | component-map, dual-path | Camada 2 |
