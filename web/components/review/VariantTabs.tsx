"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { VariantSummary } from "@/lib/types";

interface Props {
  variants: VariantSummary[];
  activeCode: string;
  onSelect: (code: string) => void;
}

export function VariantTabs({ variants, activeCode, onSelect }: Props) {
  return (
    <div className="flex items-center gap-0.5 px-3 h-10 border-b border-[var(--color-border)] bg-white overflow-x-auto">
      {variants.map((v) => {
        const isActive = v.code === activeCode;
        return (
          <button
            key={v.code}
            onClick={() => onSelect(v.code)}
            className={cn(
              "group flex items-center gap-2 px-3 h-7 rounded text-[12px] transition-colors whitespace-nowrap",
              isActive
                ? "bg-[var(--color-brand-50)] text-[var(--color-brand-700)] font-medium"
                : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]"
            )}
          >
            {v.is_approved && (
              <Check
                size={11}
                className="text-[var(--color-success-fg)]"
                strokeWidth={3}
              />
            )}
            <span>{v.label}</span>
            {v.flagged > 0 && (
              <span
                className={cn(
                  "ml-0.5 px-1 py-0 rounded text-[10px] font-mono font-semibold tabular-nums",
                  isActive
                    ? "bg-white text-[var(--color-warning-fg)]"
                    : "bg-[var(--color-warning-bg)] text-[var(--color-warning-fg)]"
                )}
              >
                {v.flagged}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
