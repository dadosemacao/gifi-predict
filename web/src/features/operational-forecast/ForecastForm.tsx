import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/input"
import { FORECAST_EXAMPLE } from "@/features/operational-forecast/forecastSample"
import { forecastFormSchema, type ForecastFormValues } from "@/schemas/forecastSchema"
import { PROCESS_FIELDS } from "@/schemas/processSchema"

type Props = {
  onSubmit: (values: ForecastFormValues) => void
  isSubmitting: boolean
  errorMessage?: string | null
}

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
