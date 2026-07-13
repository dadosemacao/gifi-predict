import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { CurvePoint } from "@/types/inference"

import { CurvesChart } from "./CurvesChart"

type Props = {
  curves: CurvePoint[]
}

export function ProductionCurvesPanel({ curves }: Props) {
  if (!curves.length) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>Curvas estimadas</CardTitle>
      </CardHeader>
      <CardContent>
        <CurvesChart data={curves} />
      </CardContent>
    </Card>
  )
}
