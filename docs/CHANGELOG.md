# Changelog — GIFI Predict

**Autor:** Emerson Antônio

---

## [0.1.0] — 2026-07-10

### Adicionado

- **Ingest Engine (Camada 2):** pacote `src/ingest/` com pipeline I1–I5 (batch + online).
- CLI `ingest` (`batch`, `scenario-validate`, `scenario-publish`, `reprocess`).
- Configuração `config/ingest.yaml` e contratos KB em `docs/kb/gifi-ingest/`.
- Testes `tests/ingest/` (13 casos, incluindo Excel real 7.573 turnos).
- Documentação: `docs/diagrams/INGEST_ENGINE.md` (diagramas de classes e fluxo).
- README atualizado com instruções de setup e uso do ingest.

### Validado

- Excel `Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx`:
  - 7.064 linhas `train_features` + 500 `holdout_features`
  - `published_with_warnings` (`INGEST_PROXY_DB`)

### Arquivado (SDD)

- Feature INGEST_ENGINE em `.claude/sdd/archive/INGEST_ENGINE/`
