# Component Map (I1–I5)

> **Purpose**: Mapa funcional do Ingest Engine e dependências  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: `docs/sketch/ingest-engine.md` §2, §5–6

## Overview

O Ingest materializa a Camada 2 (Dados e Representação). Não treina modelos nem calcula TSA. Publica artefatos versionados consumíveis pelas Camadas 3–5.

## The Concept

| ID | Nome | Função | Depende de | Alimenta |
|----|------|--------|------------|----------|
| I1 | Conectores | Ler Excel/TI/upload; hash; modo | Fontes + template L1 | I2 |
| I2 | Validação | Schema + domínio brief | Camada 1 | I3 ou quarentena |
| I3 | Transformação | Limpeza, proxy DB, Mix A/B/C | I2 ok | I4 |
| I4 | Publicação | Parquet + manifesto | I3 ok | Backbone 3/4/5 |
| I5 | Observabilidade | Logs, sinais, remediação | Todos | Operação |

```text
Fontes / Upload → I1 → I2 → I3 → I4 → Motor/Confiança/UI
                     └─ fail → quarentena ← I5 / Confiança reject
```

## Quick Reference

| Critério de pronto | Condição |
|--------------------|----------|
| Histórico | Dataset + manifesto; TC-P01/TC-A02/TC-08 |
| Cenário | Rejeição legível ou `infer_features` |
| Backbone | Só consome `published_ok` / warn aceito |

## Common Mistakes

### Wrong

Implementar I4 antes de I2 (publicar sem contrato).

### Correct

Ordem: contratos → I2 → I1 hist → I3 → I4 → I5 → I1 cenário.

## Related

- [artifact-contract.md](artifact-contract.md)
- [signal-catalog.md](signal-catalog.md)
- [../patterns/dual-path-execution.md](../patterns/dual-path-execution.md)
