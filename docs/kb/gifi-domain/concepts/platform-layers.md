# Platform Layers (Camadas 1–5)

> **Purpose**: Mapa normativo da plataforma determinística GIFI  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: `docs/sketch/analytical-backbone.md`

## Overview

Cadeia auditável **contrato → dados → cascata → aceite → uso**.  
Determinismo: mesmas entradas + mesmas regras → mesmas saídas intermediárias e finais.

## The Concept

| Camada | Nome | Função | Alimenta |
|--------|------|--------|----------|
| 1 | Domínio e Contrato | Brief, faixas, TCs, política de campeão, template cenário | 2–5 |
| 2 | Dados e Representação | Ingestão, Mix A/B/C, qualidade ponderada, dataset versionado | 3–4 |
| 3 | Motor de Simulação | Cascata Elo 1→2→3; Modos A/B; Baseline+EN+RF | 4–5 |
| 4 | Confiança e Aceite | Matrizes A∧B∧C; gate de release | 5 |
| 5 | Superfície de Uso | FastAPI serving + UI React; upload, forecast, what-if, audit SQLite | — |

```text
[1 Domínio] ──► [2 Dados] ──► [3 Motor] ──► [4 Confiança] ──► [5 Superfície]
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘  contratos / faixas / TCs
```

## Quick Reference

| Regra | Motivo |
|-------|--------|
| Sem 2 estável, não treinar 3 | Mesma representação em todos os elos |
| Sem 4, não homologar 5 | UI não substitui aceite |
| 1 permeia 2–5 | Evita regressão às divergências v1.0 |
| Release MVP | Camada 4 completa + Camada 5 mínima |

**UI até 31/08:** modo demonstração (`demo_mode=true`). Release produtivo exige A∧B∧C.

**Implementado (2026-07-13):** `src/serving/` + `web/` — três produtos (cascata, forecast, what-if direto).

## Common Mistakes

### Wrong

Homologar UI antes de Matriz A/B/C completas.

### Correct

UI em demonstração; gate produtivo só com Camada 4 completa.

## Related

- [acceptance-matrices.md](acceptance-matrices.md)
- [operational-bands.md](operational-bands.md)
- [closed-decisions.md](closed-decisions.md)
