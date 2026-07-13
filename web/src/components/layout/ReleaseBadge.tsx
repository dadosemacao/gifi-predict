import { Badge } from "@/components/ui/alert"
import type { ReleaseStatus } from "@/types/inference"

type Props = {
  status: ReleaseStatus | undefined
  isLoading: boolean
}

export function ReleaseBadge({ status, isLoading }: Props) {
  if (isLoading) return <p className="text-sm text-slate-500">Carregando release…</p>
  if (!status) return null

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <Badge
        className={
          status.demo_mode
            ? "bg-amber-100 text-amber-900"
            : "bg-emerald-100 text-emerald-900"
        }
      >
        {status.demo_mode ? "Demo" : "Release"}
      </Badge>
      <span className="text-slate-600">run_id: {status.run_id}</span>
      {status.mae_tsa_holdout != null && (
        <span className="text-slate-600">
          MAE holdout: {status.mae_tsa_holdout.toFixed(1)}
        </span>
      )}
      {status.champions.elo3 && (
        <span className="text-slate-600">Elo3: {status.champions.elo3}</span>
      )}
    </div>
  )
}
