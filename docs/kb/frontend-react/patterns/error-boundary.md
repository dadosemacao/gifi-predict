# Error Boundary

> **Purpose**: Catch render failures in feature subtrees  
> **MCP Validated**: 2026-07-09  
> **Source**: React error boundaries guidance

## When to Use

- Wrap chart-heavy features and route outlets
- Isolate Shadcn/chart library crashes from the shell

## Implementation

```tsx
import { Component, type ErrorInfo, type ReactNode } from "react"

type Props = { children: ReactNode; fallback?: ReactNode }
type State = { error: Error | null }

export class FeatureErrorBoundary extends Component<Props, State> {
  state: State = { error: null }
  static getDerivedStateFromError(error: Error) {
    return { error }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("feature_boundary", error, info.componentStack)
  }
  render() {
    if (this.state.error) {
      return this.props.fallback ?? <p>Falha ao renderizar o painel.</p>
    }
    return this.props.children
  }
}
```

```tsx
<FeatureErrorBoundary>
  <ProductionCurvesContainer jobId={id} />
</FeatureErrorBoundary>
```

Note: boundaries do **not** catch async errors in event handlers — handle those in mutations.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| granularity | per feature | Not whole app only |
| logging | console / optional telemetry | — |

## Example Usage

Route-level boundary + nested chart boundary.

## See Also

- [provider-pattern.md](provider-pattern.md)
- [container-presentational.md](container-presentational.md)
