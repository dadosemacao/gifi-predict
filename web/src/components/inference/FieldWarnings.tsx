type Props = {
  warnings: string[]
}

export function FieldWarnings({ warnings }: Props) {
  if (!warnings.length) return null
  return (
    <div
      aria-live="polite"
      className="rounded-md border border-amber-200 bg-amber-50 p-3"
      role="status"
    >
      <p className="text-sm font-medium text-amber-900">Alertas de ingestão / imputação</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm text-amber-800">
        {warnings.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
    </div>
  )
}
