# Spreadsheet Connectors Knowledge Base

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.1

> **Purpose**: Padrões de leitura Excel QM×Processo / tabelas TI / upload cenário para o I1  
> **Confidence**: 0.85 (domínio projeto + práticas genéricas de lote; sem MCP Excel dedicado)  
> **Validated**: 2026-07-09  
> **Fontes**: ingest-engine §2 I1; PRD §3.1; DECISOES D-F

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/source-modes.md](concepts/source-modes.md) | Histórico vs cenário; Excel vs TI |
| [concepts/batch-identity.md](concepts/batch-identity.md) | Nome, hash, período, timestamp |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/excel-qm-processo.md](patterns/excel-qm-processo.md) | Leitura consolidado 2018–2025 |
| [patterns/ti-interpolated-fallback.md](patterns/ti-interpolated-fallback.md) | Preferir TI; fallback Excel |
| [patterns/scenario-upload-parse.md](patterns/scenario-upload-parse.md) | Parse leve online |

### Specs

| File | Purpose |
|------|---------|
| [specs/batch-manifest-source.yaml](specs/batch-manifest-source.yaml) | Metadados de origem do lote |

---

## Quick Reference

- [quick-reference.md](quick-reference.md)

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| `gifi-ingest-engineer` | All | I1 |
| `python-developer` | patterns/* | Implementação openpyxl/pandas |
| `data-quality-analyst` | batch-identity | Pós-leitura |
