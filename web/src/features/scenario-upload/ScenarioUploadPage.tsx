import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FieldWarnings } from "@/components/inference/FieldWarnings"
import { DetractorsPanel } from "@/features/detractors-panel/DetractorsPanel"
import { ProductionCurvesPanel } from "@/features/production-curves/ProductionCurvesPanel"
import type { UploadFormValues } from "@/schemas/scenarioSchema"
import { fetchReleaseStatus } from "@/services/releaseApi"
import type { InferenceResponse } from "@/types/inference"

import { ScenarioUploadForm } from "./ScenarioUploadForm"
import { useScenarioSubmit } from "./useScenarioSubmit"

export function ScenarioUploadPage() {
  const mutation = useScenarioSubmit()
  const [result, setResult] = useState<InferenceResponse | null>(null)
  const [demo, setDemo] = useState(true)

  const releaseQuery = useQuery({
    queryKey: ["release-status"],
    queryFn: fetchReleaseStatus,
    staleTime: 60_000,
  })
  const releaseOk = releaseQuery.data?.release_ok ?? false
  // Enquanto o gate não homologa, força demonstração independentemente do toggle.
  const effectiveDemo = releaseOk ? demo : true

  const handleSubmit = async (values: UploadFormValues) => {
    setResult(null)
    const data = await mutation.mutateAsync({
      file: values.file,
      mode: values.mode,
      demo: effectiveDemo,
    })
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
            demo={effectiveDemo}
            onDemoChange={setDemo}
            releaseOk={releaseOk}
          />
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <ProductionCurvesPanel curves={result.curves} />
          <DetractorsPanel detractors={result.detractors} />
          <FieldWarnings warnings={result.warnings} />
          <Card>
            <CardHeader>
              <CardTitle>Metadados</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              <p>model_id: {result.model_id}</p>
              <p>l2_dataset_version: {result.l2_dataset_version}</p>
              <p>gate_ok: {String(result.gate_ok)}</p>
              <p>modo: {result.demo ? "demonstração" : "produção"}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
