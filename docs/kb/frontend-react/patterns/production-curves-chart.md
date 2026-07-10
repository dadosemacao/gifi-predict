# Production Curves Chart (TSA / Carga / Extrativos)

> **Purpose**: Renderizar curvas da Camada 5 a partir do DTO de inferência — sem regra de negócio  
> **Confidence**: 0.90  
> **MCP Validated**: 2026-07-09 (Context7: Recharts LineChart multi-series + ResponsiveContainer)  
> **Autor**: Emerson Antônio · **Fonte**: PRD §5; analytical-backbone Camada 5

## When to Use

- Dashboard pós-upload de cenário
- Comparar séries TSA, Carga e Extrativos no mesmo eixo X (cenário/dia)
- Homologação UI modo demonstração

## Implementation

```tsx
import type { FC } from "react"
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

export type CurveRow = {
  label: string
  tsa_dia: number
  carga_alcalina: number
  extrativo_at: number
}

type Props = {
  data: CurveRow[]
  /** Presentational only — units/labels from i18n, not domain math */
  title?: string
}

const SERIES = [
  { key: "tsa_dia" as const, name: "TSA/dia", stroke: "var(--chart-tsa, #0b5f8a)" },
  { key: "carga_alcalina" as const, name: "Carga", stroke: "var(--chart-carga, #b45309)" },
  { key: "extrativo_at" as const, name: "Extrativos", stroke: "var(--chart-ext, #15803d)" },
]

/** Presentational — receives already-fetched curves from container/hook */
export const ProductionCurvesChart: FC<Props> = ({ data, title }) => {
  return (
    <section aria-label={title ?? "Curvas de produção estimada"}>
      {title ? <h2>{title}</h2> : null}
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip />
            <Legend />
            {SERIES.map((s) => (
              <Line
                key={s.key}
                type="monotone"
                dataKey={s.key}
                name={s.name}
                stroke={s.stroke}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
```

Container (coordenação — não no chart):

```tsx
// features/dashboard/ProductionCurvesContainer.tsx
import { useQuery } from "@tanstack/react-query"
import { getInference } from "@/services/scenarioApi"
import { ProductionCurvesChart } from "./ProductionCurvesChart"

export function ProductionCurvesContainer({ jobId }: { jobId: string }) {
  const q = useQuery({ queryKey: ["inference", jobId], queryFn: () => getInference(jobId) })
  if (q.isPending) return <p>Carregando curvas…</p>
  if (q.isError) return <p role="alert">Falha ao carregar inferência</p>
  return <ProductionCurvesChart data={q.data.curves} title="Estimativas por cenário" />
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| lib | Recharts | LineChart multi-series |
| layout | ResponsiveContainer | altura fixa no wrapper |
| animação | off em homologação | previsibilidade |
| eixos | um Y compartilhado | MVP; dual-axis só se CD pedir |
| regra de negócio | proibida | só props tipadas |

## Example Usage

1. Hook/mutation chama `services/scenarioApi` (Service Layer).  
2. Container passa `curves[]` ao chart.  
3. Detratores ficam em feature separada (`features/detratores`) — um job por seção.

## Common Mistakes

### Wrong

Calcular TSA no chart; `useEffect` para “rodar simulação”; misturar fetch no presentational.

### Correct

TanStack Query no container; chart puro; schema Zod na borda do upload.

## See Also

- [container-presentational.md](container-presentational.md)
- [service-layer.md](service-layer.md)
- [custom-hooks.md](custom-hooks.md)
- ml-tabular `inference-serving`
