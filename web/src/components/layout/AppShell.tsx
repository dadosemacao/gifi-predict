import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { cn } from "@/lib/utils"
import { DemoBanner } from "@/components/layout/DemoBanner"
import { ReleaseBadge } from "@/components/layout/ReleaseBadge"
import { OperationalForecastPanel } from "@/features/operational-forecast"
import { ScenarioUploadPage } from "@/features/scenario-upload/ScenarioUploadPage"
import { WhatIfDirectPanel } from "@/features/what-if-direct"
import { fetchReleaseStatus } from "@/services/releaseApi"

type TabId = "scenario" | "forecast" | "whatif"

type Props = {
  children?: React.ReactNode
}

export function AppShell({ children }: Props) {
  const [tab, setTab] = useState<TabId>("scenario")

  const releaseQuery = useQuery({
    queryKey: ["release-status"],
    queryFn: fetchReleaseStatus,
    staleTime: 60_000,
  })

  const demoMode = releaseQuery.data?.demo_mode ?? true

  return (
    <div className="min-h-screen">
      <DemoBanner demoMode={demoMode} />
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-5xl flex-col gap-3">
          <h1 className="text-xl font-semibold">GIFI — Simulação e Forecast</h1>
          <ReleaseBadge status={releaseQuery.data} isLoading={releaseQuery.isLoading} />
          <nav className="flex gap-2" aria-label="Navegação principal">
            <TabButton
              active={tab === "scenario"}
              onClick={() => setTab("scenario")}
              label="Cenário (What-if)"
            />
            <TabButton
              active={tab === "forecast"}
              onClick={() => setTab("forecast")}
              label="Forecast operacional"
            />
            <TabButton
              active={tab === "whatif"}
              onClick={() => setTab("whatif")}
              label="What-if direto"
            />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">
        {children ??
          (tab === "scenario" ? (
            <ScenarioUploadPage />
          ) : tab === "forecast" ? (
            <OperationalForecastPanel />
          ) : (
            <WhatIfDirectPanel />
          ))}
      </main>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean
  onClick: () => void
  label: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-slate-900 text-white"
          : "bg-slate-100 text-slate-700 hover:bg-slate-200",
      )}
    >
      {label}
    </button>
  )
}
