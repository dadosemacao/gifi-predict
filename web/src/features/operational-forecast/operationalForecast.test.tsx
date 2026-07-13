import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { AppShell } from "@/components/layout/AppShell"

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
