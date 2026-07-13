import { useMutation } from "@tanstack/react-query"

import { simulateScenario } from "@/services/scenarioApi"

export function useScenarioSubmit() {
  return useMutation({
    mutationFn: ({ file, mode }: { file: File; mode: "A" | "B" }) =>
      simulateScenario(file, mode, true),
  })
}
