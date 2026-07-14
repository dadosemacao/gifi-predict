const MESSAGES: Record<string, string> = {
  unsupported_file: "Formato não suportado. Use CSV ou XLSX.",
  INGEST_SCENARIO_REJECT: "Colunas obrigatórias ausentes ou cenário inválido.",
  INGEST_MIX_FAIL: "Soma do mix fora da tolerância (deve ser 1,00).",
  mode_a_forbids_inject: "Modo A não aceita Extrativo/Carga injetados.",
  mode_mismatch: "Coluna modo diverge do Modo selecionado.",
  production_bind_blocked: "Release não homologado (A∧B∧C). Use modo demonstração.",
  validate_failed: "Falha na validação do cenário.",
  simulate_failed: "Falha na simulação.",
}

export function translateError(code: string): string {
  return MESSAGES[code] ?? code
}

export function parseApiError(detail: unknown): string {
  if (typeof detail === "string") return translateError(detail)
  if (detail && typeof detail === "object" && "code" in detail) {
    const code = String((detail as { code: string }).code)
    return translateError(code)
  }
  return "Erro inesperado."
}
