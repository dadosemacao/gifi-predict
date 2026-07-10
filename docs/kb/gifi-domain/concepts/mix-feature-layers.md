# Mix Feature Layers

> **Purpose**: Camadas A/B/C do mix de abastecimento obrigatórias na feature table  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: PRD §3.3–3.4

## Overview

O mix por sítio (A, B, C, D, MG) gera três camadas de features. Sem Camada C (entropia/HHI/dom) o aceite TC-08 / TC-P01 falha.

## The Concept

```python
# Camada A — absolutos
pct_A, pct_B, pct_C, pct_D, pct_MG  # soma ≈ 1.0

# Camada B — compostos (PRD) + agrupamentos de negócio (feature-columns)
pct_AB = pct_A + pct_B               # úmidos / crescimento rápido
pct_DMG = pct_D + pct_MG             # secos/densos (menor rendimento)
pct_ABC = pct_A + pct_B + pct_C      # crescimento rápido (PRD)
pct_CDMG = pct_C + pct_D + pct_MG    # densas/secas (PRD)
# pct_C permanece absoluto (sítio seco / restritivo)

# Camada C — diversidade
mix_entropy = shannon(pcts)
mix_hhi = sum(p**2 for p in pcts)
dom_X = 1 if pct_X > 0.50 else 0     # X in {A,B,C,D,MG}
```

## Quick Reference

| Layer | Features | Uso |
|-------|----------|-----|
| A | `pct_*` | Elo 3 + scenario |
| B | `pct_ABC`, `pct_CDMG` | orientação física |
| C | entropy, HHI, `dom_*` | diversidade / controle |

## Common Mistakes

### Wrong

Publicar só `pct_*` sem entropy/HHI.

### Correct

Feature table com A+B+C no mesmo `schema_version`.

## Related

- [data-cleaning-rules.md](data-cleaning-rules.md)
- [../patterns/volume-weighted-quality.md](../patterns/volume-weighted-quality.md)
