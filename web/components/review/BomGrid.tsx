"use client";

import { useEffect, useRef } from "react";

import { useUIStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { CabinetRow } from "@/lib/types";
import { ConfidencePill } from "./ConfidencePill";
import { EditableCell } from "./EditableCell";

interface Props {
  projectId: string;
  variantCode: string;
  rows: CabinetRow[];
}

export function BomGrid({ projectId, variantCode, rows }: Props) {
  const selectedRowIndex = useUIStore((s) => s.selectedRowIndex);
  const setSelectedRow = useUIStore((s) => s.setSelectedRow);
  const setHoveredRow = useUIStore((s) => s.setHoveredRow);

  const containerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation: J/K for next/prev, Esc to deselect
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA")
        return;

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        const next =
          selectedRowIndex === null
            ? 0
            : Math.min(rows.length - 1, selectedRowIndex + 1);
        setSelectedRow(next);
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        const next =
          selectedRowIndex === null
            ? rows.length - 1
            : Math.max(0, selectedRowIndex - 1);
        setSelectedRow(next);
      } else if (e.key === "Escape") {
        setSelectedRow(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [rows.length, selectedRowIndex, setSelectedRow]);

  // Scroll selected row into view
  useEffect(() => {
    if (selectedRowIndex === null) return;
    const el = containerRef.current?.querySelector<HTMLDivElement>(
      `[data-row-index="${selectedRowIndex}"]`
    );
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedRowIndex]);

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="h-9 px-3 flex items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)]">
        <div className="flex items-center gap-3 text-[12px]">
          <span className="font-medium text-[var(--color-text)]">
            {rows.length} rows
          </span>
          <span className="text-[var(--color-text-subtle)]">·</span>
          <span className="text-[var(--color-text-muted)]">
            <kbd className="font-mono px-1 py-0.5 rounded bg-white border border-[var(--color-border)] text-[10px]">
              J
            </kbd>
            <kbd className="ml-0.5 font-mono px-1 py-0.5 rounded bg-white border border-[var(--color-border)] text-[10px]">
              K
            </kbd>{" "}
            navigate · click W/D/H to edit
          </span>
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[36px_56px_44px_60px_1fr_180px_44px] gap-2 px-3 h-7 items-center border-b border-[var(--color-border-soft)] text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-subtle)]">
        <div>#</div>
        <div>conf</div>
        <div>cat</div>
        <div>code</div>
        <div>name</div>
        <div className="text-right">w × d × h (mm)</div>
        <div className="text-right">cite</div>
      </div>

      {/* Rows */}
      <div ref={containerRef} className="flex-1 overflow-y-auto">
        {rows.map((row) => (
          <Row
            key={row.index}
            row={row}
            isSelected={row.index === selectedRowIndex}
            onSelect={() => setSelectedRow(row.index)}
            onHover={() => setHoveredRow(row.index)}
            onLeave={() => setHoveredRow(null)}
            projectId={projectId}
            variantCode={variantCode}
          />
        ))}
      </div>
    </div>
  );
}

function Row({
  row,
  isSelected,
  onSelect,
  onHover,
  onLeave,
  projectId,
  variantCode,
}: {
  row: CabinetRow;
  isSelected: boolean;
  onSelect: () => void;
  onHover: () => void;
  onLeave: () => void;
  projectId: string;
  variantCode: string;
}) {
  const isDimensional = row.width_mm !== null;
  return (
    <div
      data-row-index={row.index}
      onClick={onSelect}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      className={cn(
        "grid grid-cols-[36px_56px_44px_60px_1fr_180px_44px] gap-2 px-3 h-9 items-center text-[13px] cursor-pointer border-b border-[var(--color-border-soft)] transition-colors",
        isSelected
          ? "bg-[var(--color-brand-50)]"
          : "hover:bg-[var(--color-surface-2)]"
      )}
    >
      <div className="text-[var(--color-text-subtle)] text-[11px] tabular-nums">
        {row.index + 1}
      </div>
      <div>
        <ConfidencePill row={row} />
      </div>
      <div>
        <span
          className={cn(
            "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold",
            row.category === "목대"
              ? "bg-[#D1FAE5] text-[#059669]"
              : "bg-[#EDE9FE] text-[#7C3AED]"
          )}
        >
          {row.category}
        </span>
      </div>
      <div>
        {row.code ? (
          <code className="text-[11px] px-1.5 py-0.5 rounded bg-[var(--color-surface-2)] text-[var(--color-text-muted)]">
            {row.code}
          </code>
        ) : (
          <span className="text-[var(--color-text-subtle)]">—</span>
        )}
      </div>
      <div className="font-medium truncate text-[var(--color-text)]">
        {row.name}
      </div>
      <div className="text-right text-[12px] text-[var(--color-text-muted)] flex items-center justify-end gap-1">
        {isDimensional ? (
          <>
            <EditableCell
              projectId={projectId}
              variantCode={variantCode}
              rowIndex={row.index}
              field="width_mm"
              value={row.width_mm}
            />
            <span className="text-[var(--color-text-subtle)]">×</span>
            <EditableCell
              projectId={projectId}
              variantCode={variantCode}
              rowIndex={row.index}
              field="depth_mm"
              value={row.depth_mm}
            />
            <span className="text-[var(--color-text-subtle)]">×</span>
            <EditableCell
              projectId={projectId}
              variantCode={variantCode}
              rowIndex={row.index}
              field="height_mm"
              value={row.height_mm}
            />
          </>
        ) : (
          <span className="text-[var(--color-text-subtle)]">—</span>
        )}
      </div>
      <div className="text-right">
        {row.rule_citation && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-rule-bg)] text-[var(--color-rule-fg)]">
            {row.rule_citation.rule_id}
          </span>
        )}
      </div>
    </div>
  );
}
