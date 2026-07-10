# Provider Pattern

> **Purpose**: Stable app-level providers (QueryClient, theme, router)  
> **MCP Validated**: 2026-07-09  
> **Source**: TanStack Query — create QueryClient once

## When to Use

- App bootstrap (`src/app/providers.tsx`)
- Sharing toast / theme / query cache

## Implementation

```tsx
import { useState, type ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  )
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

Compose router and optional TooltipProvider from Shadcn outside feature trees.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| staleTime | 30s | Inference may be longer |
| retry | 1 | Upload fails fast |

## Example Usage

`main.tsx` → `<AppProviders><Router/></AppProviders>`.

## See Also

- [../concepts/state-separation.md](../concepts/state-separation.md)
- [error-boundary.md](error-boundary.md)
