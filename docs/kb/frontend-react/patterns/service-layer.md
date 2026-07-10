# Service Layer

> **Purpose**: Isolate HTTP / inference clients from React tree  
> **MCP Validated**: 2026-07-09

## When to Use

- Talking to local backend / mock inference
- Mapping DTO ↔ UI types
- Centralizing auth headers / error codes

## Implementation

```ts
// src/services/scenarioApi.ts
import type { ScenarioPayload } from "@/types/scenario"

export type UploadJob = { id: string; status: "queued" | "done" | "rejected"; reason?: string }

export async function uploadScenario(payload: ScenarioPayload): Promise<UploadJob> {
  const res = await fetch("/api/scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `upload_failed_${res.status}`)
  }
  return res.json()
}

export async function getInference(jobId: string) {
  const res = await fetch(`/api/inference/${jobId}`)
  if (!res.ok) throw new Error(`inference_${res.status}`)
  return res.json()
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| base URL | env `VITE_API_URL` | — |
| demo mode | flag | May point to stub models |

## Example Usage

Hooks call services; components never call `fetch` directly.

## See Also

- [custom-hooks.md](custom-hooks.md)
- [schema-validation.md](schema-validation.md)
