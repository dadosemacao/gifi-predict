# Warning Admissibility Matrix

> **Purpose**: Tornar `published_with_warnings` objetivo por contexto de uso  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §3.1

## When to Use

- Antes de marcar elegibilidade Matriz A/B/C
- Gate I4 / Confiança em holdout
- Classificar warning novo (default = bloqueia)

## Implementation

| Warning | Treino | Holdout (Matriz A) | Inferência/Cenário |
|---------|--------|--------------------|--------------------|
| `INGEST_PROXY_DB` | Admitido (flag) | Admitido se ≤20% linhas; senão bloqueia | Admitido |
| `INGEST_SPARSE_LAB` | Admitido | Bloqueia se alvo/feature crítica ausente | Admitido Modo A |
| `INGEST_FILTER_INFO` | Admitido | Admitido | N/A |
| Demais novos | **Bloqueia** até listados | idem | idem |

Regra: não existe aceite ad hoc. Alinha bloqueio de release dos TCs.

## Configuration

| Setting | Default |
|---------|---------|
| `proxy_db_holdout_max_pct` | 0.20 |
| `unknown_warning_policy` | block |

## Example Usage

Holdout com 35% `db_origin=proxy` → não elegível à Matriz A; status efetivo bloqueante.

## See Also

- [../specs/warning-matrix.yaml](../specs/warning-matrix.yaml)
- [../concepts/signal-catalog.md](../concepts/signal-catalog.md)
