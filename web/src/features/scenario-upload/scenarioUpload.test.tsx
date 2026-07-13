import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { DemoBanner } from "@/components/layout/DemoBanner"
import { AppShell } from "@/components/layout/AppShell"
import { ScenarioUploadForm } from "@/features/scenario-upload/ScenarioUploadForm"
import { ScenarioUploadPage } from "@/features/scenario-upload/ScenarioUploadPage"
import { simulateScenario } from "@/services/scenarioApi"
import { fetchReleaseStatus } from "@/services/releaseApi"

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

vi.mock("@/services/scenarioApi", () => ({
  simulateScenario: vi.fn().mockResolvedValue({
    mode: "A",
    demo: true,
    gate_ok: false,
    model_id: "run-x",
    acceptance_run_id: "run-x",
    l2_dataset_version: "v0",
    curves: [],
    detractors: [],
    warnings: [],
    metrics: {},
  }),
  downloadTemplate: vi.fn(),
}))

describe("DemoBanner", () => {
  it("shows banner when demo_mode is true (AT-UI-005)", () => {
    render(<DemoBanner demoMode={true} />)
    expect(screen.getByRole("status")).toHaveTextContent(/Modo demonstração/)
  })

  it("hides banner when demo_mode is false", () => {
    render(<DemoBanner demoMode={false} />)
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
  })
})

describe("AppShell", () => {
  it("renders demo banner from release status", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={client}>
        <AppShell>
          <p>conteudo</p>
        </AppShell>
      </QueryClientProvider>,
    )
    expect(await screen.findByRole("status")).toBeInTheDocument()
    expect(screen.getByText("conteudo")).toBeInTheDocument()
  })
})

describe("ScenarioUploadForm — toggle demo/prod", () => {
  const noop = () => {}

  it("desabilita desmarcar demo quando release não homologado", () => {
    render(
      <ScenarioUploadForm
        onSubmit={noop}
        isSubmitting={false}
        demo
        onDemoChange={noop}
        releaseOk={false}
      />,
    )
    const checkbox = screen.getByRole("checkbox") as HTMLInputElement
    expect(checkbox.checked).toBe(true)
    expect(checkbox.disabled).toBe(true)
    expect(screen.getByText(/Apenas modo demonstração/)).toBeInTheDocument()
  })

  it("permite desmarcar demo quando release homologado", () => {
    const onDemoChange = vi.fn()
    render(
      <ScenarioUploadForm
        onSubmit={noop}
        isSubmitting={false}
        demo
        onDemoChange={onDemoChange}
        releaseOk
      />,
    )
    const checkbox = screen.getByRole("checkbox") as HTMLInputElement
    expect(checkbox.disabled).toBe(false)
    fireEvent.click(checkbox)
    expect(onDemoChange).toHaveBeenCalledWith(false)
  })
})

describe("ScenarioUploadPage — envio respeita release", () => {
  it("força demo=true quando release_ok=false", async () => {
    vi.mocked(fetchReleaseStatus).mockResolvedValue({
      run_id: "run-x",
      release_ok: false,
      demo_mode: true,
      l2_dataset_version: "v0",
      mae_tsa_holdout: 96.7,
      champions: { elo3: "catboost" },
    })
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={client}>
        <ScenarioUploadPage />
      </QueryClientProvider>,
    )

    const file = new File(["header\nrow"], "cenario.csv", { type: "text/csv" })
    const fileInput = screen.getByLabelText(/Planilha/) as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [file] } })
    fireEvent.click(screen.getByRole("button", { name: /Simular cenário/ }))

    await waitFor(() => expect(simulateScenario).toHaveBeenCalled())
    expect(vi.mocked(simulateScenario).mock.calls[0]).toEqual([file, "A", true])
  })
})
