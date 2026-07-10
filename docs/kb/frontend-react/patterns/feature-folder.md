# Feature Folder

> **Purpose**: Colocate GIFI UI by feature, not by technical layer only  
> **MCP Validated**: 2026-07-09

## When to Use

- New Camada 5 capabilities (upload, curves, detractors, adherence)
- Growing MVP without a god `components/` dump

## Implementation

```text
src/features/scenario-upload/
  ScenarioUploadPage.tsx       # container route
  ScenarioUploadForm.tsx       # presentational form fields
  useScenarioSubmit.ts         # feature hook
  scenarioUpload.test.tsx
  index.ts

src/features/production-curves/
  ProductionCurvesPanel.tsx
  CurvesChart.tsx
  useInferenceSeries.ts
```

Shared primitives stay in `components/ui` and `components/shared`. Cross-feature types that mirror the domain template live in `schemas/` / `types/`.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| public API | `index.ts` | Export page + hooks only |
| depth | 1 feature deep | Avoid nested feature forests |

## Example Usage

Route `/scenarios/new` lazy-loads `features/scenario-upload`.

## See Also

- [container-presentational.md](container-presentational.md)
- [../concepts/stack-and-structure.md](../concepts/stack-and-structure.md)
