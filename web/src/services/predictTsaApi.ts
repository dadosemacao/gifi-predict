import type { PredictTsaRequest, PredictTsaResponse, PredictTsaStatus } from "@/types/predictTsa"
import { parseApiError } from "@/lib/errorMessages"

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => ({}))
  return parseApiError(body.detail)
}

export async function fetchPredictTsaStatus(): Promise<PredictTsaStatus> {
  const res = await fetch("/api/predict-tsa/status")
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function postPredictTsa(body: PredictTsaRequest): Promise<PredictTsaResponse> {
  const res = await fetch("/api/predict-tsa", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}
