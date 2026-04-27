import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center font-medium rounded font-mono",
  {
    variants: {
      tone: {
        success:
          "bg-[var(--color-success-bg)] text-[var(--color-success-fg)]",
        warning:
          "bg-[var(--color-warning-bg)] text-[var(--color-warning-fg)]",
        danger:
          "bg-[var(--color-danger-bg)] text-[var(--color-danger-fg)]",
        info:
          "bg-[var(--color-info-bg)] text-[var(--color-info-fg)]",
        rule:
          "bg-[var(--color-rule-bg)] text-[var(--color-rule-fg)]",
        neutral:
          "bg-[var(--color-surface-2)] text-[var(--color-text-muted)] border border-[var(--color-border)]",
      },
      size: {
        sm: "px-1.5 py-0.5 text-[10px]",
        md: "px-2 py-0.5 text-xs",
      },
    },
    defaultVariants: {
      tone: "neutral",
      size: "sm",
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, size, ...props }: BadgeProps) {
  return (
    <span
      className={cn(badgeVariants({ tone, size }), className)}
      {...props}
    />
  );
}
