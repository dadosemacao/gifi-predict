# Relatório de Aderência e Gestão de Desvios Assistida

> **Purpose**: Estrutura normativa do entregável de encerramento (Marco 4) — não RCA automática  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09 (alinhado PRD §4.3–4.4 / §5; analytical-backbone Camada 4–5)  
> **Autor**: Emerson Antônio · **Fonte**: PRD D-11/D-12; CASOS_TESTE; champion-policy

## When to Use

- Fechar ciclo de homologação / go-no-go de release
- Documentar Matrizes A, B e C com evidências
- Apoiar analista na gestão de desvios (explicabilidade assistida)

## Implementation

Estrutura canônica do artefato (Markdown ou PDF gerado a partir de JSON):

```yaml
# adherence_report.schema.yaml (conceitual)
report_id: string
generated_at: iso8601
model_id: string
holdout: { start: "2025-05-01", end: "2025-10-30" }
gate:
  matriz_a: { mae_holdout: number, limit: 56, pass: bool }
  matriz_b: { cases_pass: int, cases_total: int, pass: bool }
  matriz_c: { method: shap|coef|permutation, scenarios_with_top3: int, pass: bool }
  release_ok: bool  # A ∧ B ∧ C
mae_by_elo:
  extrativos: number
  carga: number
  tsa: number
aux_metrics: { rmse: number, wape: number }
detractors_coverage:
  required: [TPC_verde, Extrativo_AT, Carga_Alcalina]
  optional_if_active: [Casca]
  notes: string
deviations:  # gestão assistida — sem RCA automática
  - scenario_id: string
    observed_vs_est: number
    top3: [{ feature: string, delta_tsa: number }]
    analyst_note: string | null
elo1b: NO-GO
demo_ui_only: bool
```

Checklist de aceite do relatório:

```text
[ ] MAE holdout ≤ 56 com janela D-A
[ ] RMSE e WAPE reportados
[ ] MAE_Extrativos, MAE_Carga, MAE_TSA presentes
[ ] Matriz B: vetor TC/TM com pass/fail
[ ] Matriz C: método documentado + top-3 por cenário amostrado
[ ] Mínimos TPC / Extrativo_AT / Carga cobertos na narrativa de explicabilidade
[ ] release_ok = A and B and C (nunca “quase”)
[ ] Sem promessa de RCA automática / IA genética
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Marco | 4 (out–nov/2026) | Após UI demo 31/08 |
| dono | Camada 4 | Aceite; UI só exibe |
| idioma | PT-BR | Textos do relatório |
| change request | DECISOES | Alterar limiar/método |

## Example Usage

1. `gifi-acceptance-engineer` consolida métricas + flags A/B/C.  
2. Gera JSON conforme schema → render Markdown/PDF.  
3. Analista preenche `analyst_note` nos desvios (assistido).  
4. `ship-agent` / arquivo em `reports/` com `model_id` e hash do manifesto.

## Common Mistakes

### Wrong

Usar UI demo como prova de Matriz A; omitir MAE por elo; tratar top-3 como RCA causal automática.

### Correct

Relatório amarra evidências A∧B∧C; desvios = decomposição assistida; Elo 1b permanece NO-GO no MVP.

## See Also

- [../concepts/acceptance-matrices.md](../concepts/acceptance-matrices.md)
- [champion-policy.md](champion-policy.md)
- ml-tabular `matriz-c-detractors` · `artifact-packaging`
