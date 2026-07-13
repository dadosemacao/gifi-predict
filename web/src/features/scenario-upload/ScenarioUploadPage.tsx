import { useState } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DetractorsPanel } from "@/features/detractors-panel/DetractorsPanel"
import { ProductionCurvesPanel } from "@/features/production-curves/ProductionCurvesPanel"
import type { UploadFormValues } from "@/schemas/scenarioSchema"
import type { InferenceResponse } from "@/types/inference"

import { ScenarioUploadForm } from "./ScenarioUploadForm"
import { useScenarioSubmit } from "./useScenarioSubmit"

export function ScenarioUploadPage() {
  const mutation = useScenarioSubmit()
  const [result, setResult] = useState<InferenceResponse | null>(null)

  const handleSubmit = async (values: UploadFormValues) => {
    setResult(null)
    const data = await mutation.mutateAsync(values)
    setResult(data)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload de cenário</CardTitle>
        </CardHeader>
        <CardContent>
          <ScenarioUploadForm
            onSubmit={handleSubmit}
            isSubmitting={mutation.isPending}
            errorMessage={mutation.error?.message ?? null}
          />
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <ProductionCurvesPanel curves={result.curves} />
          <DetractorsPanel detractors={result.detractors} />
          <Card>
            <CardHeader>
              <CardTitle>Metadados</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              <p>model_id: {result.model_id}</p>
              <p>l2_dataset_version: {result.l2_dataset_version}</p>
              <p>gate_ok: {String(result.gate_ok)}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
