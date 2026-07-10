# Feature Column Contract

> **Purpose**: Lista fixa de colunas da feature table L2 (negócio → canônico)  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: lista de features CD 2026-07-09; PRD §3; `specs/feature-columns.yaml`

## Overview

O contrato operacional (§4.2 do ingest-engine) exige lista fixa de features com tipo e unidade. A lista de negócio (processo, Lab/SGF, abastecimento/mix) é mapeada para nomes canônicos; Mix Camada C do PRD permanece obrigatória no artefato mesmo quando omitida na lista bruta.

## The Concept

| Grupo negócio | Exemplos canônicos |
|---------------|-------------------|
| Processo | `TSA_dia` (alvo), `Carga_Alcalina`, `Kappa` |
| Lab / SGF | `DB_SGF`, `DB_LAB`, `Secura_pct`, `Casca_pct`, `Extrativo_*` |
| Abastecimento | `TPC`, `Idade`, `VMI` + flags de faixa |
| Mix | `pct_*`, `pct_AB`, `pct_DMG`, `pct_ABC`, `pct_CDMG`, diversity |

```yaml
# VMI contínuo + 3 flags (mutuamente exclusivas)
VMI: float
vmi_le_021:  VMI <= 0.21
vmi_021_025: 0.21 < VMI <= 0.25
vmi_gt_025:  VMI > 0.25
```

## Quick Reference

| Regra | Valor |
|-------|-------|
| Spec | `specs/feature-columns.yaml` |
| Coluna nova | exige `schema_version` major |
| Casca | feature se medida; Elo 1b NO-GO |
| Proxy DB | `db_origin=proxy` |

## Common Mistakes

### Wrong

Publicar só `A+B`, `C`, `D+MG` sem `pct_A..pct_MG` e sem Camada C.

### Correct

Absolutos + compostos de negócio + compostos PRD + entropy/HHI/`dom_*`.

## Related

- [../specs/feature-columns.yaml](../specs/feature-columns.yaml)
- [artifact-contract.md](artifact-contract.md)
- `docs/kb/gifi-domain/concepts/mix-feature-layers.md`
