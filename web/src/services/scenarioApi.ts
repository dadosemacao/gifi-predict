import type { InferenceResponse, ValidateResponse } from "@/types/inference"
import { parseApiError } from "@/lib/errorMessages"

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => ({}))
  return parseApiError(body.detail)
}

export async function validateScenario(
  file: File,
  mode: "A" | "B",
): Promise<ValidateResponse> {
  const body = new FormData()
  body.append("file", file)
  body.append("mode", mode)
  const res = await fetch("/api/scenario/validate", { method: "POST", body })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function simulateScenario(
  file: File,
  mode: "A" | "B",
  demo = true,
): Promise<InferenceResponse> {
  const body = new FormData()
  body.append("file", file)
  body.append("mode", mode)
  body.append("demo", String(demo))
  const res = await fetch("/api/simulate", { method: "POST", body })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

export async function downloadTemplate(): Promise<void> {
  const res = await fetch("/api/template")
  if (!res.ok) throw new Error("Falha ao baixar template")
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "template_cenario_v0.csv"
  a.click()
  URL.revokeObjectURL(url)
}
