import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { AppShell } from "@/components/layout/AppShell"
import { LocalDetractorsList } from "@/features/what-if-direct/LocalDetractorsList"
import { SensitivityChart } from "@/features/what-if-direct/SensitivityChart"
import type { LocalDetractor, PredictTsaResponse, SensitivityPoint } from "@/types/predictTsa"

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

const postPredictTsa = vi.fn()

vi.mock("@/services/predictTsaApi", () => ({
  fetchPredictTsaStatus: vi.fn().mockResolvedValue({
    run_id: "2026-07-13T104544Z",
    family: "lasso",
    product: "what_if_direct",
    holdout_mae: 89.0,
    holdout_r2: 0.2,
    interval_80_coverage: 0,
    artifact_path: "models/primeira_base/tsa_lasso.joblib",
    features: [],
  }),
  postPredictTsa: (...args: unknown[]) => postPredictTsa(...args),
}))

vi.mock("@/services/forecastApi", () => ({
  fetchForecastStatus: vi.fn().mockResolvedValue({
    run_id: "x",
    family: "extratrees",
    anchor: "TSA_roll3",
    product: "forecast_operacional",
    holdout_mae: 67,
    holdout_r2: 0.2,
    interval_80_coverage: 0.7,
    artifact_path: "x",
  }),
  postForecast: vi.fn(),
}))

const ANALYTICS_RESULT: PredictTsaResponse = {
  product: "what_if_direct",
  model_id: "run-tsa",
  family: "lasso",
  tsa_dia: 3410,
  disclaimer:
    "Previsão sem histórico. Explicabilidade assistida — não é Matriz C e não libera o gate de release.",
  metrics: { mae_holdout: 89, r2_holdout: 0.2, interval_80_coverage: 0 },
  field_origins: { carga_alcalina: "medido" },
  warnings: [],
  sensitivity: [
    { value: 465, tsa_dia: 3380 },
    { value: 490, tsa_dia: 3410 },
    { value: 515, tsa_dia: 3440 },
  ],
  detractors: [
    { feature: "db_sgf", delta_tsa: -12.5, method: "local_ablation" },
    { feature: "tpc", delta_tsa: 8.1, method: "local_ablation" },
    { feature: "idade", delta_tsa: -3.2, method: "local_ablation" },
  ],
  sensitivity_variable: "db_sgf",
  sensitivity_steps: 3,
}

function renderShell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <AppShell />
    </QueryClientProvider>,
  )
}

describe("What-if analytics UI", () => {
  beforeEach(() => {
    postPredictTsa.mockReset()
    postPredictTsa.mockResolvedValue(ANALYTICS_RESULT)
  })

  it("AT-PTA-007: mostra curva e top-3 após submit com analytics", async () => {
    renderShell()
    fireEvent.click(await screen.findByRole("button", { name: "What-if direto" }))
    expect(await screen.findByText(/Incluir analytics/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /Estimar TSA/ }))
    await waitFor(() => {
      expect(postPredictTsa).toHaveBeenCalled()
    })
    const opts = postPredictTsa.mock.calls[0][1]
    expect(opts.includeAnalytics).toBe(true)
    expect(await screen.findByText(/Curva de sensibilidade/)).toBeInTheDocument()
    expect(screen.getByText(/Top-3 impacto/)).toBeInTheDocument()
    expect(screen.getAllByText(/não é Matriz C/i).length).toBeGreaterThanOrEqual(1)
  })
})

describe("SensitivityChart / LocalDetractorsList", () => {
  it("renderiza pontos e lista", () => {
    const points: SensitivityPoint[] = [
      { value: 465, tsa_dia: 3300 },
      { value: 515, tsa_dia: 3400 },
    ]
    const detractors: LocalDetractor[] = [
      { feature: "db_sgf", delta_tsa: -5, method: "local_ablation" },
    ]
    render(
      <>
        <SensitivityChart data={points} variableLabel="DB SGF" />
        <LocalDetractorsList detractors={detractors} />
      </>,
    )
    expect(screen.getByLabelText(/Sensibilidade TSA/)).toBeInTheDocument()
    expect(screen.getByText("DB SGF")).toBeInTheDocument()
  })
})
