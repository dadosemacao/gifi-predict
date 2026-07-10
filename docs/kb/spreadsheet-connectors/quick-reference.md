# Spreadsheet Connectors Quick Reference

**Autor:** Emerson Antônio · **Data:** 2026-07-09 · **Validated:** 2026-07-09

## Fontes

| Fonte | Modo | Prioridade |
|-------|------|------------|
| Tabelas limpas/interpoladas TI | Histórico | Preferencial (se existir) |
| Excel QM×Processo consolidado | Histórico | Fallback MVP |
| Upload planilha cenário | Cenário online | Instância do template L1 |

## Identidade do lote

| Campo | Obrigatório |
|-------|-------------|
| `batch_name` | Sim |
| `source_hash` | Sim (conteúdo) |
| `period_start` / `period_end` | Histórico |
| `ingested_at` | Sim |
| `mode` | `historical` \| `scenario` |

## Sinais I1

| Situação | Código |
|----------|--------|
| Arquivo ausente/ilegível | `INGEST_SOURCE_MISSING` |
| Template cenário inválido | `INGEST_SCENARIO_REJECT` |

## Pitfalls

| Don't | Do |
|-------|-----|
| Hash só do nome do arquivo | Hash do conteúdo |
| Assumir TI sempre disponível | Fallback Excel |
| Parse pesado na UI path | Só checagens leves online |
