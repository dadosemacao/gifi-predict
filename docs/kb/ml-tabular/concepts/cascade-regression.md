# Cascade Regression (Elo 1→2→3)

> **Purpose**: Stage-wise supervised regressors for Caminho da Ida  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §4.1

## Overview

Three mandatory stages compose Extrativos → Carga → TSA.  
Error compounds in Mode A; Mode B isolates stages for diagnosis.

## The Concept

```text
[Planejamento]
  Sítio + Idade + Mix + TPC + Volume + DB_SGF (+ Kappa)
        ├─ Elo 1  → Extrativo_AT
        ├─ Elo 1b → % Casca          # NO-GO MVP
        ├─ Elo 2  → Carga Alcalina   # uses Elo1 (or inject)
        └─ Elo 3  → TSA/dia          # uses Elo1+2 (+ inject)
```

| Elo | y | X (MVP) |
|-----|---|---------|
| 1 | Extrativo_AT | Sítio, Idade, mix features |
| 2 | Carga | Extrativo_AT, TPC, DB_SGF |
| 3 | TSA/dia | Mix A/B/C, DB_LAB*, Extrativo, Carga, TPC, VMI, Volume, Kappa (+Casca if measured) |

`* DB_LAB = Lab or 0.985 × DB_SGF`

```python
STAGE_ORDER = ("elo1_extrativo", "elo2_carga", "elo3_tsa")
# Never train elo3 labels with future calendar leakage into holdout.
```

## Quick Reference

| Mode | Extrativo / Carga source |
|------|--------------------------|
| A | Predicted by prior elos |
| B | Injected measured values |

## Common Mistakes

### Wrong

Training Elo1b Casca for MVP release path.

### Correct

Omit Elo1b; optional Casca only as Elo3 feature when measured.

## Related

- [elasticnet-vs-rf.md](elasticnet-vs-rf.md)
- [../patterns/mode-a-b-inference.md](../patterns/mode-a-b-inference.md)
