import type { ForecastRequest, ForecastResponse, ForecastStatus } from "@/types/forecast"
import { parseApiError } from "@/lib/errorMessages"

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => ({}))
  return parseApiError(body.detail)
}

export async function fetchForecastStatus(): Promise<ForecastStatus> {
  const res = await fetch("/api/forecast/status")
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function postForecast(body: ForecastRequest): Promise<ForecastResponse> {
  const res = await fetch("/api/forecast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}
