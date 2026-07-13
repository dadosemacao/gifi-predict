import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input, Label } from "@/components/ui/input"
import { FORECAST_EXAMPLE } from "@/features/operational-forecast/forecastSample"
import {
  PROCESS_FIELDS,
  processVariablesSchema,
  type ProcessVariablesValues,
} from "@/schemas/processSchema"
import { fetchPredictTsaStatus, postPredictTsa } from "@/services/predictTsaApi"
import type { PredictTsaResponse } from "@/types/predictTsa"

const EXAMPLE: ProcessVariablesValues = {
  carga_alcalina: FORECAST_EXAMPLE.carga_alcalina,
  kappa: FORECAST_EXAMPLE.kappa,
  db_sgf: FORECAST_EXAMPLE.db_sgf,
  db_lab: FORECAST_EXAMPLE.db_lab,
  secura_pct: FORECAST_EXAMPLE.secura_pct,
  casca_pct: FORECAST_EXAMPLE.casca_pct,
  extrativo_total: FORECAST_EXAMPLE.extrativo_total,
  extrativo_at: FORECAST_EXAMPLE.extrativo_at,
  extrativo_sgf: FORECAST_EXAMPLE.extrativo_sgf,
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
  const mutation = useMutation({ mutationFn: postPredictTsa })
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>What-if direto (sem histórico TSA)</CardTitle>
          <p className="text-sm text-slate-600">
            Informe apenas as 17 variáveis de processo. Não exige histórico de turnos — útil para
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
          <CardContent className="space-y-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-600">TSA estimada (t/dia)</p>
              <p className="text-3xl font-semibold text-slate-900">{fmt(result.tsa_dia)}</p>
            </div>
            <p className="text-sm text-amber-800">{result.disclaimer}</p>
            <p className="text-sm text-slate-600">
              Família: {result.family} · run_id: {result.model_id}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
