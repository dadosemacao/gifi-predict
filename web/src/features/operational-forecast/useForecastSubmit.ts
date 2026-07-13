import { useMutation } from "@tanstack/react-query"

import { toForecastRequest, type ForecastFormValues } from "@/schemas/forecastSchema"
import { postForecast } from "@/services/forecastApi"

export function useForecastSubmit() {
  return useMutation({
    mutationFn: (values: ForecastFormValues) => postForecast(toForecastRequest(values)),
  })
}
