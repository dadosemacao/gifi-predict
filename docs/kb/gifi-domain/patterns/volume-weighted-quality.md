# Volume-Weighted Quality

> **Purpose**: Ponderar atributos de qualidade pelo volume abastecido  
> **Validated**: 2026-07-09  
> **Fonte**: PRD §3.4; decisão D-C

## When to Use

- Agregar qualidade do nível turno para dia
- Publicar features de treino/inferência com DB, Extrativo, Casca
- Evitar média aritmética simples enviesada por turnos leves

## Implementation

```python
def weighted_mean(values, volumes):
    """média_ponderada = Σ(valor_i × volume_i) / Σ volume_i"""
    v = sum(volumes)
    if v <= 0:
        raise ValueError("volume total deve ser > 0")
    return sum(x * w for x, w in zip(values, volumes)) / v

# Variáveis obrigatórias quando existirem:
# DB_LAB, Extrativo_AT, % Casca (se medida), demais qualidade do abastecimento
# Volume: SOMAR na agregação turno→dia (não ponderar)
# TSA: meta diária conforme regra de negócio (não média simples cega)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `weight_col` | `Volume_m3` | Peso |
| `quality_cols` | DB_LAB, Extrativo_AT, Casca | Cuando disponíveis |
| `null_policy` | drop_pair | Excluir par valor/peso nulo do numerador |

## Example Usage

```python
day_db = weighted_mean(turnos["DB_LAB"], turnos["Volume_m3"])
day_volume = turnos["Volume_m3"].sum()
```

## See Also

- [../concepts/mix-feature-layers.md](../concepts/mix-feature-layers.md)
- [../concepts/closed-decisions.md](../concepts/closed-decisions.md)
