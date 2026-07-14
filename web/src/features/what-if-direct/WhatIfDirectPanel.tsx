import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { FieldOriginsPanel } from "@/components/inference/FieldOriginsPanel"
import { FieldWarnings } from "@/components/inference/FieldWarnings"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input, Label } from "@/components/ui/input"
import { FORECAST_EXAMPLE } from "@/features/operational-forecast/forecastSample"
import { LocalDetractorsList } from "@/features/what-if-direct/LocalDetractorsList"
import { SensitivityChart } from "@/features/what-if-direct/SensitivityChart"
import {
  PROCESS_FIELDS,
  processVariablesSchema,
  type ProcessVariablesValues,
} from "@/schemas/processSchema"
import { fetchPredictTsaStatus, postPredictTsa } from "@/services/predictTsaApi"
import {
  SENSITIVITY_VARIABLE_OPTIONS,
  type PredictTsaResponse,
} from "@/types/predictTsa"

const EXAMPLE: ProcessVariablesValues = {
  carga_alcalina: FORECAST_EXAMPLE.carga_alcalina,
  kappa: FORECAST_EXAMPLE.kappa,
  prod_alcali_class: FORECAST_EXAMPLE.prod_alcali_class,
  db_sgf: FORECAST_EXAMPLE.db_sgf,
  casca_pct: FORECAST_EXAMPLE.casca_pct,
  extrativo_at: FORECAST_EXAMPLE.extrativo_at,
  tpc: FORECAST_EXAMPLE.tpc,
  idade: FORECAST_EXAMPLE.idade,
  vmi_le_021: FORECAST_EXAMPLE.vmi_le_021,
  vmi_021_025: FORECAST_EXAMPLE.vmi_021_025,
  vmi_gt_025: FORECAST_EXAMPLE.vmi_gt_025,
  pct_ab: FORECAST_EXAMPLE.pct_ab,
  pct_c: FORECAST_EXAMPLE.pct_c,
  pct_dmg: FORECAST_EXAMPLE.pct_dmg,
}

function fmt(n: number) {
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })
}

export function WhatIfDirectPanel() {
  const [result, setResult] = useState<PredictTsaResponse | null>(null)
  const [includeAnalytics, setIncludeAnalytics] = useState(true)
  const [sensitivityVariable, setSensitivityVariable] = useState("db_sgf")
  const mutation = useMutation({
    mutationFn: (values: ProcessVariablesValues) =>
      postPredictTsa(values, {
        includeAnalytics,
        sensitivityVariable: includeAnalytics ? sensitivityVariable : undefined,
      }),
  })
  const statusQuery = useQuery({
    queryKey: ["predict-tsa-status"],
    queryFn: fetchPredictTsaStatus,
    staleTime: 60_000,
    retry: 1,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProcessVariablesValues>({
    resolver: zodResolver(processVariablesSchema),
    defaultValues: EXAMPLE,
  })

  const onSubmit = async (values: ProcessVariablesValues) => {
    setResult(null)
    setResult(await mutation.mutateAsync(values))
  }

  const variableLabel =
    SENSITIVITY_VARIABLE_OPTIONS.find((o) => o.value === (result?.sensitivity_variable ?? sensitivityVariable))
      ?.label ?? sensitivityVariable

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>What-if direto (sem histórico TSA)</CardTitle>
          <p className="text-sm text-slate-600">
            Informe as 13 variáveis de processo oficiais (Camada 3). Não exige histórico de turnos — útil para
            sliders e testes rápidos. Precisão menor que o forecast operacional.
          </p>
          {statusQuery.data && (
            <p className="text-sm text-slate-600">
              Modelo: <span className="font-medium">{statusQuery.data.family}</span> (
              {statusQuery.data.run_id})
              {statusQuery.data.holdout_mae != null && (
                <> · MAE holdout {statusQuery.data.holdout_mae.toFixed(1)}</>
              )}
            </p>
          )}
          {statusQuery.isError && (
            <Alert>Modelo what-if indisponível. Verifique se o serving está ativo.</Alert>
          )}
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {PROCESS_FIELDS.map(({ name, label, step }) => (
                <div key={name} className="space-y-1">
                  <Label htmlFor={`wif-${name}`}>{label}</Label>
                  <Input id={`wif-${name}`} type="number" step={step ?? "any"} {...register(name)} />
                  {errors[name] && (
                    <p className="text-sm text-red-600">{String(errors[name]?.message)}</p>
                  )}
                </div>
              ))}
            </div>
            <div className="flex flex-wrap items-end gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={includeAnalytics}
                  onChange={(e) => setIncludeAnalytics(e.target.checked)}
                />
                Incluir analytics (curva + top-3)
              </label>
              {includeAnalytics && (
                <div className="space-y-1">
                  <Label htmlFor="wif-sensitivity-var">Variável de sensibilidade</Label>
                  <select
                    id="wif-sensitivity-var"
                    className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm"
                    value={sensitivityVariable}
                    onChange={(e) => setSensitivityVariable(e.target.value)}
                  >
                    {SENSITIVITY_VARIABLE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            {mutation.error && <Alert>{mutation.error.message}</Alert>}
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Calculando…" : "Estimar TSA"}
              </Button>
              <Button type="button" variant="outline" onClick={() => reset(EXAMPLE)}>
                Carregar exemplo
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Resultado</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-600">TSA estimada (t/dia)</p>
              <p className="text-3xl font-semibold text-slate-900">{fmt(result.tsa_dia)}</p>
            </div>
            <p className="text-sm text-amber-800">{result.disclaimer}</p>
            <p className="text-sm text-slate-600">
              Família: {result.family} · run_id: {result.model_id}
            </p>
            <FieldOriginsPanel fieldOrigins={result.field_origins} />
            <FieldWarnings warnings={result.warnings} />
            {result.sensitivity && result.sensitivity.length > 0 && (
              <SensitivityChart data={result.sensitivity} variableLabel={variableLabel} />
            )}
            {result.detractors && <LocalDetractorsList detractors={result.detractors} />}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
