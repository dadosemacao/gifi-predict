import type { FC } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { SensitivityPoint } from "@/types/predictTsa"

type Props = {
  data: SensitivityPoint[]
  variableLabel: string
}

export const SensitivityChart: FC<Props> = ({ data, variableLabel }) => (
  <section aria-label={`Sensibilidade TSA × ${variableLabel}`}>
    <h3 className="mb-2 text-base font-medium">Curva de sensibilidade ({variableLabel})</h3>
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="value" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="tsa_dia"
            name="TSA/dia"
            stroke="#0b5f8a"
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </section>
)
