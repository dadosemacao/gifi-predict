# Scenario Template Contract

> **Purpose**: Quebrar circularidade UI↔Ingest — template nasce na Camada 1  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §4.1 obj.3; DECISOES D-E

## When to Use

- Bootstrap do conector I1 Cenário (antes da UI existir)
- Validação online de upload (Modo A/B)
- Versionamento `template_cenario_v0` (+ semver)
- Especificação publicada: `docs/kb/gifi-domain/specs/template_cenario_v0.yaml`

## Implementation

```text
Ordem de bootstrap:
1. Domínio publica template_cenario_vN (contrato + colunas + unidades)
2. Ingest I2 valida instâncias contra template
3. UI Camada 5 só envia instância preenchida

Regra: Camada 5 NÃO é dona do schema do template.
```

```yaml
template_id: template_cenario_v0
modes: [A, B]
required_common:
  - cenario_id
  - linha
  - sitio_ou_mix_pcts
  - idade
  - tpc_dias
  - volume_m3
  - db_sgf
  - kappa
mode_A_forbidden_inject:
  - extrativo_at
  - carga_alcalina
mode_B_allows_inject:
  - extrativo_at
  - carga_alcalina
  - db_lab
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `owner` | Camada 1 Domínio | Fonte da verdade |
| `reject_code` | `INGEST_SCENARIO_REJECT` | Upload inválido |
| `path` | online síncrono | Sem quarentena |

## Example Usage

Upload Modo A com coluna `carga_alcalina` preenchida → rejeitar com motivo legível.

## See Also

- [../concepts/mode-a-b.md](../concepts/mode-a-b.md)
- `docs/kb/gifi-ingest/patterns/dual-path-execution.md`
