import type { ReleaseStatus } from "@/types/inference"

export async function fetchReleaseStatus(): Promise<ReleaseStatus> {
  const res = await fetch("/api/release-status")
  if (!res.ok) throw new Error("release_status_failed")
  return res.json()
}
