import { cn } from "@/lib/utils"
import type { FieldOrigin, FieldOrigins } from "@/types/forecast"

const FIELD_LABELS: Record<keyof FieldOrigins, string> = {
  carga_alcalina: "Carga alcalina",
  kappa: "Kappa",
  prod_alcali_class: "Prod. álcali",
  db_sgf: "DB SGF",
  casca_pct: "% Casca",
  extrativo_at: "Extrativo AT",
  tpc: "TPC",
  idade: "Idade",
  vmi_le_021: "VMI ≤ 0,21",
  vmi_021_025: "VMI 0,21–0,25",
  vmi_gt_025: "VMI > 0,25",
  pct_ab: "A + B",
  pct_dmg: "D + MG",
}

const ORIGIN_LABEL: Record<FieldOrigin, string> = {
  medido: "Medido",
  proxy: "Proxy (Tier A)",
  estimado: "Estimado (Tier B)",
}

const ORIGIN_STYLE: Record<FieldOrigin, string> = {
  medido: "bg-emerald-100 text-emerald-800",
  proxy: "bg-sky-100 text-sky-800",
  estimado: "bg-amber-100 text-amber-800",
}

type Props = {
  fieldOrigins: FieldOrigins
}

export function FieldOriginsPanel({ fieldOrigins }: Props) {
  const entries = Object.entries(fieldOrigins).filter(([, origin]) => origin != null) as Array<
    [keyof FieldOrigins, FieldOrigin]
  >
  if (!entries.length) return null

  return (
    <div className="rounded-md border border-slate-200 p-3">
      <p className="text-sm font-medium text-slate-700">Origem dos campos</p>
      <p className="mt-0.5 text-xs text-slate-500">
        Medido = enviado no request; Proxy = regra Tier A; Estimado = imputer Tier B.
      </p>
      <ul className="mt-2 flex flex-wrap gap-2">
        {entries.map(([field, origin]) => (
          <li
            key={field}
            className="flex items-center gap-1.5 rounded-md border border-slate-200 px-2 py-1 text-xs"
          >
            <span className="text-slate-600">{FIELD_LABELS[field]}</span>
            <span className={cn("rounded px-1.5 py-0.5 font-medium", ORIGIN_STYLE[origin])}>
              {ORIGIN_LABEL[origin]}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
