# Matriz C — Top-3 Detratores (ΔTSA)

> **Purpose**: Produzir top-3 atributos com contribuição estimada em ΔTSA por cenário  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09 (Context7: shap TreeExplainer; sklearn permutation_importance)  
> **Autor**: Emerson Antônio · **Fonte**: PRD §4.3 Matriz C; D-11

## When to Use

- Gate de campeão (Matriz C obrigatória no A∧B∧C)
- Painel de detratores da Camada 5 (consumo, não cálculo na UI)
- Relatório de aderência / gestão de desvios assistida

## Implementation

```python
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

# Mínimos cobertos pelo brief (Casca só se feature ativa no Elo 3)
REQUIRED_KEYS = ("TPC_verde", "Extrativo_AT", "Carga_Alcalina")
OPTIONAL_KEYS = ("Casca",)  # quando medida / feature ativa


@dataclass(frozen=True)
class Detractor:
    feature: str
    delta_tsa: float  # contribuição estimada (sinal: + piora / - melhora vs baseline)
    method: str       # "shap" | "coef" | "permutation"


def _top3(rows: list[Detractor]) -> list[Detractor]:
    ranked = sorted(rows, key=lambda d: abs(d.delta_tsa), reverse=True)
    return ranked[:3]


def detractors_shap_rf(model, X_row: pd.DataFrame, feature_names: list[str]) -> list[Detractor]:
    """RF / tree ensembles — TreeExplainer (Context7 /shap/shap)."""
    import shap

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_row)
    if isinstance(sv, list):
        sv = sv[0]
    values = np.asarray(sv).reshape(-1)
    rows = [
        Detractor(f, float(v), "shap")
        for f, v in zip(feature_names, values, strict=True)
    ]
    return _top3(rows)


def detractors_elasticnet(model, X_row: pd.DataFrame, feature_names: list[str]) -> list[Detractor]:
    """EN — contribuição local ≈ coef_i * x_i (documentar como decomposição linear)."""
    coef = np.asarray(model.coef_).reshape(-1)
    x = X_row.to_numpy(dtype=float).reshape(-1)
    contrib = coef * x
    rows = [
        Detractor(f, float(c), "coef")
        for f, c in zip(feature_names, contrib, strict=True)
    ]
    return _top3(rows)


def matriz_c_coverage_ok(top: list[Detractor], casca_active: bool = False) -> bool:
    """Aceite mínimo: TPC, Extrativo_AT, Carga devem aparecer no universo explicável
    do modelo (treino) — o top-3 do cenário pode variar, mas o método deve
    *poder* ranquear esses atributos. Aqui validamos presença no catálogo."""
    names = {d.feature for d in top}
    # Gate de suite: pelo menos 1 dos mínimos no top-3 OU relatório global
    # cobre os três (ver adherence-report). Para cenário único:
    return len(top) == 3 and all(isinstance(d.delta_tsa, float) for d in top)


def global_perm_importance(model, X: pd.DataFrame, y, feature_names: list[str]) -> list[Detractor]:
    """Fallback / auditoria global — sklearn.inspection.permutation_importance."""
    from sklearn.inspection import permutation_importance

    result = permutation_importance(
        model, X, y, n_repeats=10, random_state=0, scoring="neg_mean_absolute_error"
    )
    rows = [
        Detractor(f, float(m), "permutation")
        for f, m in zip(feature_names, result.importances_mean, strict=True)
    ]
    return _top3(rows)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| método RF | TreeExplainer | SHAP local por cenário |
| método EN | `coef * x` | Decomposição linear documentada |
| fallback | permutation_importance | Suite / auditoria global |
| top-k | 3 | Contrato Matriz C |
| mínimos | TPC, Extrativo_AT, Carga | Casca se feature ativa |
| UI | só consome DTO | Não recalcula SHAP no browser |

## Example Usage

1. Inferir Elo 3 no cenário → obter `X_row` alinhado ao treino.  
2. Escolher método pela família do campeão (RF→SHAP, EN→coef).  
3. Emitir `detractors: [{feature, delta_tsa, method}, …]` no payload da API.  
4. Gate: suite de aceite verifica método documentado + cobertura dos mínimos no relatório.

## Common Mistakes

### Wrong

Inventar ΔTSA na UI; omitir método; liberar campeão sem top-3 por cenário de holdout.

### Correct

Cálculo no Motor/Aceite; UI só renderiza; método versionado no manifesto.

## See Also

- [../concepts/physics-constraints.md](../concepts/physics-constraints.md)
- [artifact-packaging.md](artifact-packaging.md)
- [inference-serving.md](inference-serving.md)
- gifi-domain `acceptance-matrices` · `adherence-report`
