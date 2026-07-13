import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { Alert } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ForecastFormValues } from "@/schemas/forecastSchema"
import { fetchForecastStatus } from "@/services/forecastApi"
import type { ForecastResponse } from "@/types/forecast"

import { ForecastForm } from "./ForecastForm"
import { ForecastResultPanel, ForecastStatusBadge } from "./ForecastResultPanel"
import { useForecastSubmit } from "./useForecastSubmit"

export function OperationalForecastPanel() {
  const mutation = useForecastSubmit()
  const [result, setResult] = useState<ForecastResponse | null>(null)

  const statusQuery = useQuery({
    queryKey: ["forecast-status"],
    queryFn: fetchForecastStatus,
    staleTime: 60_000,
    retry: 1,
  })

  const handleSubmit = async (values: ForecastFormValues) => {
    setResult(null)
    const data = await mutation.mutateAsync(values)
    setResult(data)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Forecast operacional (Produto A)</CardTitle>
          <p className="text-sm text-slate-600">
            Previsão do próximo turno com histórico recente de TSA + variáveis de processo. Separado
            do what-if de cenário (Modo A/B).
          </p>
          {statusQuery.data && <ForecastStatusBadge status={statusQuery.data} />}
          {statusQuery.isError && (
            <Alert>Modelo de forecast indisponível. Verifique se o serving está ativo.</Alert>
          )}
        </CardHeader>
        <CardContent>
          <ForecastForm
            onSubmit={handleSubmit}
            isSubmitting={mutation.isPending}
            errorMessage={mutation.error?.message ?? null}
          />
        </CardContent>
      </Card>

      {result && <ForecastResultPanel result={result} />}
    </div>
  )
}
