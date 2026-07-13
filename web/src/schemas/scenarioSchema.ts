import { z } from "zod"

export const scenarioModeSchema = z.enum(["A", "B"])

export const uploadFormSchema = z.object({
  mode: scenarioModeSchema,
  file: z
    .custom<File>((v) => v instanceof File, "Arquivo obrigatório")
    .refine(
      (f) => /\.(csv|xlsx|xls)$/i.test(f.name),
      "Use CSV ou XLSX conforme template v0",
    ),
})

export type UploadFormValues = z.infer<typeof uploadFormSchema>
