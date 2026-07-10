# Target and Framing

> **Purpose**: Definir o problema analítico do GIFI sem ambiguidade  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: `docs/PRD_GIFI_v1.1.md` §1–2

## Overview

O GIFI estima produção de celulose (TSA/dia) a partir de planejamento de abastecimento, sem lags temporais. Serve ao Caminho da Ida (simulação) e a explicabilidade assistida de desvios.

## The Concept

| Dimensão | Definição |
|----------|-----------|
| Alvo | `TSA/dia` (digestor), meta diária a partir de turnos |
| Horizonte | Cenários futuros de mix / abastecimento |
| Entradas | Mix sítios A–MG, qualidade ponderada, processo fixo/estimado |
| Restrição dura | Sem lags / janelas móveis / autocorrelação |
| Decisão de negócio | Ajustar frentes e mix com base na TSA estimada |

```text
[Planejamento] → Mix + qualidade + processo → Cascata Elo1→2→3 → TSA/dia
                      (sem lags)
```

## Quick Reference

| In-scope MVP | Out-of-scope |
|--------------|--------------|
| Cascata Ida, EN+RF, UI local | Caminho da Volta |
| Mix A/B/C completo | Cloud tempo real |
| Explicabilidade Top-3 | RCA automática / NN obrigatória |

## Common Mistakes

### Wrong

Modelo com lag de TSA ontem ou média móvel de mix.

### Correct

Apenas variáveis disponíveis no planejamento de talhões ainda não cortados.

## Related

- [data-cleaning-rules.md](data-cleaning-rules.md)
- [mode-a-b.md](mode-a-b.md)
- [closed-decisions.md](closed-decisions.md)
