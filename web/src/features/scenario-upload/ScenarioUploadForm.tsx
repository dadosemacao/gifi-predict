import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input, Label } from "@/components/ui/input"
import { uploadFormSchema, type UploadFormValues } from "@/schemas/scenarioSchema"
import { downloadTemplate } from "@/services/scenarioApi"

type Props = {
  onSubmit: (values: UploadFormValues) => void
  isSubmitting: boolean
  errorMessage?: string | null
}

export function ScenarioUploadForm({ onSubmit, isSubmitting, errorMessage }: Props) {
  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<UploadFormValues>({
    resolver: zodResolver(uploadFormSchema),
    defaultValues: { mode: "A" },
  })

  const mode = watch("mode")

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-2">
        <Label htmlFor="mode">Modo</Label>
        <select
          id="mode"
          className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
          value={mode}
          onChange={(e) => setValue("mode", e.target.value as "A" | "B")}
        >
          <option value="A">Modo A — Integração</option>
          <option value="B">Modo B — Isolamento</option>
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="file">Planilha (template v0)</Label>
        <Input
          id="file"
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) setValue("file", file, { shouldValidate: true })
          }}
        />
        {errors.file && <p className="text-sm text-red-600">{errors.file.message}</p>}
      </div>

      {errorMessage && <Alert>{errorMessage}</Alert>}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Simulando…" : "Simular cenário"}
        </Button>
        <Button type="button" variant="outline" onClick={() => downloadTemplate()}>
          Baixar template CSV
        </Button>
      </div>
    </form>
  )
}
