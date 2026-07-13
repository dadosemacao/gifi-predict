import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/input"
import { FORECAST_EXAMPLE } from "@/features/operational-forecast/forecastSample"
import { forecastFormSchema, type ForecastFormValues } from "@/schemas/forecastSchema"

type Props = {
  onSubmit: (values: ForecastFormValues) => void
  isSubmitting: boolean
  errorMessage?: string | null
}

const PROCESS_FIELDS: Array<{ name: keyof ForecastFormValues; label: string; step?: string }> = [
  { name: "carga_alcalina", label: "Carga alcalina" },
  { name: "kappa", label: "Kappa" },
  { name: "prod_alcali_class", label: "Prod. álcali (0=baixo, 1=normal)" },
  { name: "db_sgf", label: "DB SGF" },
  { name: "casca_pct", label: "% Casca" },
  { name: "extrativo_at", label: "Extrativo AT" },
  { name: "tpc", label: "TPC" },
  { name: "idade", label: "Idade" },
  { name: "vmi_le_021", label: "VMI ≤ 0,21", step: "1" },
  { name: "vmi_021_025", label: "VMI 0,21–0,25", step: "1" },
  { name: "vmi_gt_025", label: "VMI > 0,25", step: "1" },
  { name: "pct_ab", label: "A + B" },
  { name: "pct_c", label: "C (aux. imputer)" },
  { name: "pct_dmg", label: "D + MG" },
]

export function ForecastForm({ onSubmit, isSubmitting, errorMessage }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ForecastFormValues>({
    resolver: zodResolver(forecastFormSchema),
    defaultValues: FORECAST_EXAMPLE,
  })

  return (
    <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-2">
        <Label htmlFor="tsa_history_text">Histórico TSA (turnos recentes)</Label>
        <p className="text-xs text-slate-500">
          Informe ao menos 7 valores em ordem cronológica, separados por vírgula. O último valor é
          o turno mais recente.
        </p>
        <Input
          id="tsa_history_text"
          {...register("tsa_history_text")}
          placeholder="3289, 3250, 3250, 3250, 3400, 3450, 3470"
        />
        {errors.tsa_history_text && (
          <p className="text-sm text-red-600">{errors.tsa_history_text.message}</p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {PROCESS_FIELDS.map(({ name, label, step }) => (
          <div key={name} className="space-y-1">
            <Label htmlFor={name}>{label}</Label>
            <Input id={name} type="number" step={step ?? "any"} {...register(name)} />
            {errors[name] && (
              <p className="text-sm text-red-600">{String(errors[name]?.message)}</p>
            )}
          </div>
        ))}
      </div>

      {errorMessage && <Alert>{errorMessage}</Alert>}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Calculando…" : "Prever TSA (próximo turno)"}
        </Button>
        <Button type="button" variant="outline" onClick={() => reset(FORECAST_EXAMPLE)}>
          Carregar exemplo
        </Button>
      </div>
    </form>
  )
}
