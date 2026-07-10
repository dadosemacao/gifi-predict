# Container / Presentational

> **Purpose**: Split data orchestration from pure rendering  
> **MCP Validated**: 2026-07-09

## When to Use

- Feature pages that fetch or mutate
- Reusable charts/tables across modes

## Implementation

```tsx
// Container
export function ProductionCurvesContainer({ jobId }: { jobId: string }) {
  const { data, isPending, error } = useInferenceSeries(jobId)
  if (isPending) return <CurvesSkeleton />
  if (error) return <CurvesError message={error.message} />
  return <CurvesChart series={data.series} mode={data.mode} />
}

// Presentational — no Query, no domain gates
export function CurvesChart({
  series,
  mode,
}: {
  series: { t: string; tsa: number }[]
  mode: "A" | "B"
}) {
  return (
    <section data-mode={mode}>
      {/* chart lib binding only */}
      <pre>{JSON.stringify(series.slice(0, 3))}</pre>
    </section>
  )
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| props | serializable | Easy Storybook/RTL |
| side effects | container/hooks only | — |

## Example Usage

Storybook covers `CurvesChart` with fixtures; integration tests cover container + MSW.

## See Also

- [../concepts/no-business-in-ui.md](../concepts/no-business-in-ui.md)
- [custom-hooks.md](custom-hooks.md)
