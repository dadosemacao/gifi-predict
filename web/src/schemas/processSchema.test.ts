import { describe, expect, it } from "vitest"

import { processVariablesSchema } from "@/schemas/processSchema"

const VALID = {
  carga_alcalina: 19.0,
  kappa: 16.5,
  prod_alcali_class: 1,
  db_sgf: 490,
  casca_pct: 0.8,
  tpc: 60,
  idade: 7,
}

describe("processVariablesSchema — faixas oficiais", () => {
  it("aceita um payload dentro das faixas", () => {
    expect(processVariablesSchema.safeParse(VALID).success).toBe(true)
  })

  it("aceita valores nas bordas inclusivas", () => {
    const borders = { ...VALID, carga_alcalina: 17.5, kappa: 15.0, db_sgf: 465, casca_pct: 1.5, tpc: 45 }
    expect(processVariablesSchema.safeParse(borders).success).toBe(true)
    const upper = { ...VALID, carga_alcalina: 21.0, kappa: 18.5, db_sgf: 515 }
    expect(processVariablesSchema.safeParse(upper).success).toBe(true)
  })

  it.each([
    ["carga_alcalina", 16],
    ["carga_alcalina", 22],
    ["kappa", 14.9],
    ["kappa", 18.6],
    ["db_sgf", 464],
    ["db_sgf", 516],
    ["casca_pct", 1.6],
    ["tpc", 44],
  ])("rejeita %s = %s fora da faixa", (field, value) => {
    const result = processVariablesSchema.safeParse({ ...VALID, [field]: value })
    expect(result.success).toBe(false)
  })

  it("aceita prod_alcali_class como string enum", () => {
    expect(processVariablesSchema.safeParse({ ...VALID, prod_alcali_class: "baixo" }).success).toBe(
      true,
    )
  })
})
