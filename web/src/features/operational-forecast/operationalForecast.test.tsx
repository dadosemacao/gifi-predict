import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { AppShell } from "@/components/layout/AppShell"
import { ForecastResultPanel } from "@/features/operational-forecast/ForecastResultPanel"
import type { ForecastResponse } from "@/types/forecast"

vi.mock("@/services/releaseApi", () => ({
  fetchReleaseStatus: vi.fn().mockResolvedValue({
    run_id: "2026-07-10T10:54:42.849161Z",
    release_ok: false,
    demo_mode: true,
    l2_dataset_version: "2026-07-10T07:35:10Z",
    mae_tsa_holdout: 96.7,
    champions: { elo3: "catboost" },
  }),
}))

vi.mock("@/services/forecastApi", () => ({
  fetchForecastStatus: vi.fn().mockResolvedValue({
    run_id: "2026-07-13T104544Z",
    family: "extratrees",
    anchor: "TSA_roll3",
    product: "forecast_operacional",
    holdout_mae: 67.6,
    holdout_r2: 0.25,
    interval_80_coverage: 0.71,
    artifact_path: "models/primeira_base/forecast_2026-07-13T104544Z/forecast_extratrees.joblib",
  }),
  postForecast: vi.fn(),
}))

function renderShell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <AppShell />
    </QueryClientProvider>,
  )
}

describe("AppShell forecast tab", () => {
  it("shows forecast panel when tab is selected", async () => {
    renderShell()
    await screen.findByText(/Upload de cenário/)
    fireEvent.click(screen.getByRole("button", { name: "Forecast operacional" }))
    expect(await screen.findByText(/Forecast operacional \(Produto A\)/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Prever TSA/ })).toBeInTheDocument()
  })
})

const FORECAST_RESULT: ForecastResponse = {
  product: "forecast_operacional",
  model_id: "run-x",
  family: "extratrees",
  anchor_name: "TSA_roll3",
  tsa_dia: 3400,
  tsa_dia_lo: 3350,
  tsa_dia_hi: 3450,
  anchor: 3390,
  residual: 10,
  baselines: { lag1: 3380, roll3: 3390, roll7: 3395 },
  metrics: { mae_holdout: 67.6, r2_holdout: 0.25, interval_80_coverage: 0.71 },
  field_origins: { carga_alcalina: "medido", extrativo_at: "estimado" },
  warnings: ["INGEST_PROXY_EXTR: extrativo estimado"],
}

describe("ForecastResultPanel", () => {
  it("mostra origem dos campos e warnings", () => {
    render(<ForecastResultPanel result={FORECAST_RESULT} />)
    expect(screen.getByText("Origem dos campos")).toBeInTheDocument()
    expect(screen.getByText("Estimado (Tier B)")).toBeInTheDocument()
    expect(screen.getByText(/extrativo estimado/)).toBeInTheDocument()
  })
})
