import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SENSITIVITY_VARIABLE_OPTIONS, type LocalDetractor } from "@/types/predictTsa"

type Props = {
  detractors: LocalDetractor[]
}

function labelFor(feature: string): string {
  return SENSITIVITY_VARIABLE_OPTIONS.find((o) => o.value === feature)?.label ?? feature
}

export function LocalDetractorsList({ detractors }: Props) {
  if (!detractors.length) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top-3 impacto (ablação local)</CardTitle>
        <p className="text-sm text-slate-600">
          ΔTSA vs cenário informado — não é Matriz C do aceite.
        </p>
      </CardHeader>
      <CardContent>
        <ol className="space-y-2">
          {detractors.map((d) => (
            <li key={d.feature} className="flex justify-between text-sm">
              <span className="font-medium">{labelFor(d.feature)}</span>
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
