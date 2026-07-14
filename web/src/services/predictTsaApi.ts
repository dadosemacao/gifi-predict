import type {
  PostPredictTsaOptions,
  PredictTsaRequest,
  PredictTsaResponse,
  PredictTsaStatus,
} from "@/types/predictTsa"
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

export async function postPredictTsa(
  body: PredictTsaRequest,
  opts: PostPredictTsaOptions = {},
): Promise<PredictTsaResponse> {
  const qs = new URLSearchParams()
  if (opts.includeAnalytics) qs.set("include_analytics", "true")
  if (opts.sensitivityVariable) qs.set("sensitivity_variable", opts.sensitivityVariable)
  if (opts.sensitivitySteps != null) qs.set("sensitivity_steps", String(opts.sensitivitySteps))
  if (opts.runId) qs.set("run_id", opts.runId)
  const suffix = qs.toString() ? `?${qs}` : ""
  const res = await fetch(`/api/predict-tsa${suffix}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}
