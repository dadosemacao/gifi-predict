# GIFI Domain Knowledge Base

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.2

> **Purpose**: Contratos normativos da Camada 1 (SSOT) — camadas 1–5, faixas, Matrizes A/B/C, Modo A/B, decisões  
> **Confidence**: 0.95 (fontes normativas do projeto)  
> **MCP Validated**: 2026-07-09  
> **Fontes**: PRD v1.1, analytical-backbone, DECISOES_GIFI, REFERENCIA_FAIXAS, MAPA_COMPONENTES

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/platform-layers.md](concepts/platform-layers.md) | Camadas 1–5 da plataforma |
| [concepts/target-and-framing.md](concepts/target-and-framing.md) | Alvo TSA/dia, sem lags, Caminho da Ida |
| [concepts/operational-bands.md](concepts/operational-bands.md) | Faixas + fator 0,985 |
| [concepts/acceptance-matrices.md](concepts/acceptance-matrices.md) | Matrizes A/B/C + MAE≤56 |
| [concepts/data-cleaning-rules.md](concepts/data-cleaning-rules.md) | Filtro TSA, kg/m³, mix |
| [concepts/mix-feature-layers.md](concepts/mix-feature-layers.md) | Definição Camadas A/B/C |
| [concepts/mode-a-b.md](concepts/mode-a-b.md) | Integração vs isolamento |
| [concepts/closed-decisions.md](concepts/closed-decisions.md) | Holdout, Elo 1b NO-GO |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/mix-abc-features.md](patterns/mix-abc-features.md) | Código Mix A/B/C |
| [patterns/turno-dia-aggregation.md](patterns/turno-dia-aggregation.md) | Agregação turno→dia |
| [patterns/champion-policy.md](patterns/champion-policy.md) | Política de campeão |
| [patterns/scenario-column-contract.md](patterns/scenario-column-contract.md) | Colunas Modo A/B |
| [patterns/volume-weighted-quality.md](patterns/volume-weighted-quality.md) | Médias por volume |
| [patterns/scenario-template-contract.md](patterns/scenario-template-contract.md) | Template v0 Camada 1 |
| [patterns/adherence-report.md](patterns/adherence-report.md) | Relatório de aderência / desvios assistidos |

### Specs

| File | Purpose |
|------|---------|
| [specs/operational-ranges.yaml](specs/operational-ranges.yaml) | Faixas máquina |
| [specs/domain-rules.yaml](specs/domain-rules.yaml) | Regras numéricas |

## Quick Reference

- [quick-reference.md](quick-reference.md)

## Key Concepts

| Concept | Description |
|---------|-------------|
| **SSOT Domínio** | Brief + faixas + TCs + template cenário |
| **Gate A∧B∧C** | Release só com estatística + física + explicabilidade |
| **Elo 1b** | NO-GO MVP; casca só feature medida no Elo 3 |
| **Holdout** | 2025-05→2025-10; treino até 2025-04 |

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| `gifi-domain-specialist` | All | Guardião normativo |
| `gifi-simulation-engineer` | acceptance, champion, mode-a-b | Motor Camada 3 |
| `gifi-acceptance-engineer` | acceptance-matrices, champion, adherence-report | Gate Camada 4 |
| `gifi-ingest-engineer` | cleaning, specs, template | Contrato I2/I3 |
