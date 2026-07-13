import { cn } from "@/lib/utils"
import type { HTMLAttributes } from "react"

export function Alert({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="alert"
      className={cn("rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800", className)}
      {...props}
    />
  )
}

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        className,
      )}
      {...props}
    />
  )
}
