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

import type { CurvePoint } from "@/types/inference"

type Props = {
  data: CurvePoint[]
  title?: string
}

const SERIES = [
  { key: "tsa_dia" as const, name: "TSA/dia", stroke: "#0b5f8a" },
  { key: "carga_alcalina" as const, name: "Carga", stroke: "#b45309" },
  { key: "extrativo_at" as const, name: "Extrativos", stroke: "#15803d" },
]

export const CurvesChart: FC<Props> = ({ data, title }) => (
  <section aria-label={title ?? "Curvas de produção estimada"}>
    {title ? <h3 className="mb-2 text-base font-medium">{title}</h3> : null}
    <div className="h-[360px] w-full">
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
