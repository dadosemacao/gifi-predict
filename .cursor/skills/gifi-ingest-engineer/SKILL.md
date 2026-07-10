---
name: gifi-ingest-engineer
description: >
  Dono do Ingest Engine GIFI (I1–I5): conectores, validação, Mix/proxy DB,
  publicação Parquet+manifesto, sinais INGEST_*, quarentena e remediação.
  Use when building or changing ingest, dual-path batch/online, or L2 artifacts.
---

# Skill — GIFI Ingest Engineer

**Autor:** Emerson Antônio  
**Data:** 2026-07-09

## When to Use

- Implementar ou alterar I1–I5
- Dual-path batch histórico vs validação online de cenário
- Catálogo de sinais / matriz de warnings / remediação
- Publicar `train_features` / `holdout_features` / `infer_features`
- Conectores Excel QM×Processo, TI ou upload de cenário

## Instructions

1. Ler o agente canônico: `.cursor/agents/gifi-ingest-engineer.md`
2. KB-first: `docs/kb/gifi-ingest/` + plano `docs/sketch/ingest-engine.md`
3. Norma ambígua → skill `gifi-domain-specialist` / KB `gifi-domain`
4. Conectores → `docs/kb/spreadsheet-connectors/`
5. Ordem de build: contratos → I2 → I1 hist → I3 → I4 → I5 → I1 cenário
6. Warning fora da matriz = bloqueante (sem aceite ad hoc)
7. Responder no formato do agente (Path + Sinais + Publish + Confidence)

## KB Entry Points

| Path | Uso |
|------|-----|
| `docs/kb/gifi-ingest/quick-reference.md` | Dual-path / status |
| `docs/kb/gifi-ingest/specs/signal-catalog.yaml` | Códigos |
| `docs/kb/gifi-ingest/specs/warning-matrix.yaml` | Admissibilidade |
| `docs/kb/gifi-ingest/specs/artifact-contract.yaml` | Contrato L2 |
| `docs/kb/spreadsheet-connectors/` | I1 |

## Do Not

- Misturar SLA online com quarentena batch
- Sobrescrever last-good
- Inventar códigos de sinal
- Usar nome `sentinel-engine` (obsoleto)
- Treinar modelos / calcular TSA
