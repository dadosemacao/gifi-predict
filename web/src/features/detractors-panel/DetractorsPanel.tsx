import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Detractor } from "@/types/inference"

type Props = {
  detractors: Detractor[]
}

export function DetractorsPanel({ detractors }: Props) {
  if (!detractors.length) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top-3 detratores (linha-âncora)</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-2">
          {detractors.map((d) => (
            <li key={d.feature} className="flex justify-between text-sm">
              <span className="font-medium">{d.feature}</span>
              <span>
                ΔTSA {d.delta_tsa.toFixed(1)} ({d.method})
              </span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
