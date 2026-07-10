# Inference Serving — Upload → Curvas + Detratores

> **Purpose**: API local que materializa Camada 3→5 (cenário → TSA/Carga/Extrativos + Matriz C)  
> **Confidence**: 0.90  
> **MCP Validated**: 2026-07-09 (Context7: FastAPI UploadFile + response_model; Pydantic)  
> **Autor**: Emerson Antônio · **Fonte**: analytical-backbone Camada 5; PRD §5

## When to Use

- Homologação UI (modo demonstração) até 31/08
- Bind produtivo só com manifesto `gate: A_and_B_and_C`
- Validação leve online (schema/mix) antes da cascata — sem quarentena batch

## Implementation

```python
from __future__ import annotations

from typing import Annotated, Literal
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="GIFI Inference", version="0.1.0")


class CurvePoint(BaseModel):
    label: str  # dia / cenário id
    tsa_dia: float
    carga_alcalina: float
    extrativo_at: float


class DetractorOut(BaseModel):
    feature: str
    delta_tsa: float
    method: Literal["shap", "coef", "permutation"]


class InferenceResponse(BaseModel):
    mode: Literal["A", "B"]
    demo: bool
    model_id: str
    gate_ok: bool
    curves: list[CurvePoint]
    detractors: list[DetractorOut] = Field(max_length=3)
    warnings: list[str] = []


@app.post("/api/simulate", response_model=InferenceResponse)
async def simulate(
    file: Annotated[UploadFile, File(description="Planilha template Modo A/B")],
    mode: Annotated[Literal["A", "B"], Form()] = "A",
    demo: Annotated[bool, Form()] = True,
) -> InferenceResponse:
    if file.filename is None or not file.filename.lower().endswith((".xlsx", ".csv")):
        raise HTTPException(status_code=400, detail="unsupported_file")

    raw = await file.read()
    # 1) parse + validação leve (schema/mix/faixas) — dual-path online
    # 2) infer_cascade (mode-a-b-inference)
    # 3) matriz-c-detractors no Elo 3
    # 4) se not demo and not gate_ok → 403
    raise NotImplementedError("wire parse + cascade + detractors + champion load")
```

Contrato mínimo de serviço (TypeScript espelhado em `services/`):

```ts
export type InferenceResponse = {
  mode: "A" | "B"
  demo: boolean
  model_id: string
  gate_ok: boolean
  curves: { label: string; tsa_dia: number; carga_alcalina: number; extrativo_at: number }[]
  detractors: { feature: string; delta_tsa: number; method: "shap" | "coef" | "permutation" }[]
  warnings: string[]
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `demo=true` | UI Marco 2 | Permite modelo não-gated |
| `demo=false` | exige manifesto A∧B∧C | Release produtivo |
| parse | openpyxl/pandas | Template Camada 1 |
| validação | leve / síncrona | Sem remediação humana no loop |
| auth | local MVP | Sem cloud obrigatória |

## Example Usage

1. UI faz `multipart/form-data` com arquivo + `mode` + `demo`.  
2. Backend valida colunas (Zod no front + Pydantic/schema no back).  
3. Resposta alimenta Recharts (`curves`) e lista de detratores.  
4. `gate_ok=false` + `demo=false` → HTTP 403 com motivo.

## Common Mistakes

### Wrong

Treinar no request; colocar regra de MAE na UI; misturar path batch de ingest com SLA online.

### Correct

Só inferência + validação leve; treino/artefato fora do request; dual-path do ingest-engine.

## See Also

- [mode-a-b-inference.md](mode-a-b-inference.md)
- [matriz-c-detractors.md](matriz-c-detractors.md)
- [artifact-packaging.md](artifact-packaging.md)
- frontend-react `service-layer` · `production-curves-chart`
