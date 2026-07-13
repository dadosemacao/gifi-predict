import { useMutation } from "@tanstack/react-query"

import { simulateScenario } from "@/services/scenarioApi"

type SubmitArgs = {
  file: File
  mode: "A" | "B"
  demo: boolean
}

export function useScenarioSubmit() {
  return useMutation({
    mutationFn: ({ file, mode, demo }: SubmitArgs) => simulateScenario(file, mode, demo),
  })
}
