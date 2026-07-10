# Champion Policy

> **Purpose**: Selecionar campeão EN/RF (+ baseline) com gate físico e explicável  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §4.2–4.3; analytical-backbone Camada 1/4

## When to Use

- Comparar Baseline vs ElasticNet vs RandomForest
- Decidir release do artefato do Motor (Camada 3 → 4)
- Experimento NN opcional (só campeão se vencer A∧B∧C)

## Implementation

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CandidateScore:
    name: str
    mae_holdout: float
    matriz_b_ok: bool
    matriz_c_ok: bool
    interpretability_rank: int  # 1 = mais interpretável

def is_release_ready(c: CandidateScore, mae_limit: float = 56.0) -> bool:
    matriz_a = c.mae_holdout <= mae_limit
    return matriz_a and c.matriz_b_ok and c.matriz_c_ok

def select_champion(cands: list[CandidateScore]) -> CandidateScore | None:
    eligible = [c for c in cands if is_release_ready(c)]
    if not eligible:
        return None
    # Melhor MAE; empate → interpretabilidade > complexidade
    eligible.sort(key=lambda c: (c.mae_holdout, c.interpretability_rank))
    return eligible[0]
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `mae_limit` | 56 | Matriz A |
| famílias MVP | Baseline, EN, RF | NN opcional |
| empate | interpretabilidade | > complexidade |
| Elo 1b | NO-GO MVP | não entra no campeão |

## Example Usage

Treinar candidatos no holdout D-A; rodar TCs Matriz B; gerar top-3 Matriz C; só então serializar campeão.

## See Also

- [../concepts/acceptance-matrices.md](../concepts/acceptance-matrices.md)
- [scenario-column-contract.md](scenario-column-contract.md)
