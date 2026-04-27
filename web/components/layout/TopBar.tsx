"use client";

import Link from "next/link";
import { Search, Bell } from "lucide-react";

export function TopBar({ projectName }: { projectName?: string }) {
  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-[var(--color-border)] bg-white">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold text-[15px] tracking-tight"
        >
          <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-[var(--color-brand-600)] text-white text-[11px] font-bold">
            K
          </span>
          <span className="text-[var(--color-text)]">KBOM</span>
        </Link>
        {projectName && (
          <>
            <span className="text-[var(--color-text-subtle)]">/</span>
            <span className="text-[14px] font-medium text-[var(--color-text)]">
              {projectName}
            </span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            const event = new KeyboardEvent("keydown", {
              key: "k",
              metaKey: true,
              bubbles: true,
            });
            document.dispatchEvent(event);
          }}
          className="flex items-center gap-2 px-2.5 h-7 rounded border border-[var(--color-border)] bg-[var(--color-surface-2)] text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-slate-300 transition-colors"
        >
          <Search size={12} />
          <span>Search</span>
          <kbd className="ml-2 px-1 py-0.5 rounded text-[10px] font-mono bg-white border border-[var(--color-border)]">
            ⌘K
          </kbd>
        </button>
        <button className="h-7 w-7 inline-flex items-center justify-center rounded text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)]">
          <Bell size={14} />
        </button>
        <div className="flex items-center gap-2 ml-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-brand-100)] text-[var(--color-brand-700)] text-[11px] font-semibold">
            PK
          </span>
          <span className="text-xs text-[var(--color-text-muted)]">Park</span>
        </div>
      </div>
    </header>
  );
}
