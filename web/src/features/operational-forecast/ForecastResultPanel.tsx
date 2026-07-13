import { FieldOriginsPanel } from "@/components/inference/FieldOriginsPanel"
import { FieldWarnings } from "@/components/inference/FieldWarnings"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ForecastResponse, ForecastStatus } from "@/types/forecast"

type Props = {
  result: ForecastResponse
}

function fmt(n: number) {
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })
}

export function ForecastResultPanel({ result }: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Previsão TSA — próximo turno</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-600">TSA prevista (t/dia)</p>
            <p className="text-3xl font-semibold text-slate-900">{fmt(result.tsa_dia)}</p>
            <p className="mt-1 text-sm text-slate-600">
              Intervalo 80%: {fmt(result.tsa_dia_lo)} — {fmt(result.tsa_dia_hi)}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Baseline lag1" value={fmt(result.baselines.lag1)} />
            <Metric label="Baseline roll3" value={fmt(result.baselines.roll3)} />
            <Metric label="Baseline roll7" value={fmt(result.baselines.roll7)} />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <Metric label="Âncora (roll3)" value={fmt(result.anchor)} />
            <Metric label="Resíduo ML" value={fmt(result.residual)} />
          </div>

          <FieldOriginsPanel fieldOrigins={result.field_origins} />
          <FieldWarnings warnings={result.warnings} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Modelo</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-600">
          <p>Produto: {result.product}</p>
          <p>Família: {result.family}</p>
          <p>run_id: {result.model_id}</p>
          {result.metrics.mae_holdout != null && (
            <p>MAE holdout: {fmt(result.metrics.mae_holdout)}</p>
          )}
          {result.metrics.r2_holdout != null && (
            <p>R² holdout: {result.metrics.r2_holdout.toFixed(3)}</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium text-slate-900">{value}</p>
    </div>
  )
}

export function ForecastStatusBadge({ status }: { status: ForecastStatus }) {
  return (
    <p className="text-sm text-slate-600">
      Forecast bindado: <span className="font-medium">{status.family}</span> ({status.run_id})
      {status.holdout_mae != null && (
        <>
          {" "}
          · MAE holdout {status.holdout_mae.toFixed(1)}
        </>
      )}
    </p>
  )
}
