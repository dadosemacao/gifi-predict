# Scenario Column Contract (Modo A/B)

> **Purpose**: Colunas permitidas/proibidas no upload por modo  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §4.1; DECISOES D-E

## When to Use

- Validar planilha de cenário (I1 online / Camada 5)
- Gerar checklist de rejeição legível
- Versionar `template_cenario_vN`

## Implementation

```python
from __future__ import annotations

COMMON_REQUIRED = {
    "cenario_id", "linha", "idade", "tpc_dias", "volume_m3", "db_sgf", "kappa",
}
# Mix: pct_A..pct_MG OU sitiocomposição equivalente no template
MIX_COLS = {"pct_A", "pct_B", "pct_C", "pct_D", "pct_MG"}
MODE_A_FORBIDDEN = {"extrativo_at", "carga_alcalina"}  # estimados pela cascata
MODE_B_OPTIONAL = {"extrativo_at", "carga_alcalina", "db_lab"}

def validate_scenario_row(row: dict, mode: str) -> list[str]:
    errors: list[str] = []
    cols = {k.lower() for k in row}
    missing = COMMON_REQUIRED - cols
    if missing:
        errors.append(f"missing: {sorted(missing)}")
    if mode.upper() == "A":
        injected = MODE_A_FORBIDDEN & {k for k, v in row.items()
                                       if v is not None and str(v).strip() != ""}
        if injected:
            errors.append(f"Modo A forbids inject: {sorted(injected)}")
    return errors
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| owner | Camada 1 | Template é artefato de Domínio |
| reject | `INGEST_SCENARIO_REJECT` | Código de sinal |
| Modo A | integração | Extrativo/Carga estimados |
| Modo B | isolamento | Injeção permitida |

## Example Usage

Upload Modo A com `carga_alcalina` preenchida → rejeitar antes de inferência.

## See Also

- [scenario-template-contract.md](scenario-template-contract.md)
- [../concepts/mode-a-b.md](../concepts/mode-a-b.md)
