type Props = { demoMode: boolean }

export function DemoBanner({ demoMode }: Props) {
  if (!demoMode) return null
  return (
    <div
      role="status"
      className="border border-amber-400 bg-amber-100 px-4 py-2 text-sm text-amber-950"
    >
      Modo demonstração — não homologado para uso operacional. Resultados usam candidato L3
      sem bind produtivo (release_ok=false).
    </div>
  )
}
