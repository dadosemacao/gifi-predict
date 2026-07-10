# GIFI Ingest Quick Reference

**Autor:** Emerson Antônio · **Data:** 2026-07-09 · **Validated:** 2026-07-09

## Dual-path

| Path | SLA | Remediação |
|------|-----|------------|
| Histórico batch | min–horas | Sim (ciclo completo) |
| Cenário online | segundos | Não (só feedback UI) |

## Status de publicação

| Status | Backbone pode consumir? |
|--------|-------------------------|
| `published_ok` | Sim |
| `published_with_warnings` | Só se todos admitidos no contexto |
| quarentena / fail | Não; last-good permanece |

## Sinais (macro)

| Código | Sev |
|--------|-----|
| `INGEST_SCHEMA_FAIL` | Bloq |
| `INGEST_MIX_FAIL` | Bloq |
| `INGEST_UNIT_FAIL` | Bloq |
| `INGEST_SOURCE_MISSING` | Bloq |
| `INGEST_SCENARIO_REJECT` | Bloq |
| `ACCEPT_DATA_REJECT` | Bloq* |
| `INGEST_PROXY_DB` | Aviso |
| `INGEST_SPARSE_LAB` | Aviso |
| `INGEST_FILTER_INFO` | Info |

\*gerado na Camada 4.

## Artefatos

| Nome | Destino |
|------|---------|
| `train_features` | Motor |
| `holdout_features` | Confiança |
| `infer_features` | Motor/UI |
| manifesto JSON | todos |

## Colunas (resumo)

| Grupo | Canônicos |
|-------|-----------|
| Processo | `TSA_dia`, `Carga_Alcalina`, `Kappa` |
| Lab/SGF | `DB_SGF`, `DB_LAB`, `Secura_pct`, `Casca_pct`, `Extrativo_*` |
| Abastecimento | `TPC`, `Idade`, `VMI` + `vmi_*` flags |
| Mix | `pct_*`, `pct_AB`, `pct_DMG`, `pct_ABC`, `pct_CDMG`, Camada C |
| Spec | `specs/feature-columns.yaml` |

## Ordem de build

`contratos → I2 → I1 hist → I3 → I4 → I5 → I1 cenário`

## Pitfalls

| Don't | Do |
|-------|-----|
| Prometer UI “instantânea” via batch | Online só checagens leves |
| Warning fora da matriz | Default = bloqueia |
| Sobrescrever last-good | Quarentena + novo hash |
