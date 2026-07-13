import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { DemoBanner } from "@/components/layout/DemoBanner"
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
