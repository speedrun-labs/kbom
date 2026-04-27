"use client";

import { useState } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/lib/store";
import type { CabinetRow, Segment } from "@/lib/types";

interface Props {
  projectId: string;
  pageNumber: number;
  variantLabel: string;
  rows: CabinetRow[];
  segments: Segment[];
  imageWidthPx: number;
  imageHeightPx: number;
}

export function BlueprintCanvas({
  projectId,
  pageNumber,
  variantLabel,
  rows,
  segments,
  imageWidthPx,
  imageHeightPx,
}: Props) {
  const [zoom, setZoom] = useState(1);
  const imgUrl = api.blueprintImageUrl(projectId, pageNumber);

  const hoveredRowIndex = useUIStore((s) => s.hoveredRowIndex);
  const selectedRowIndex = useUIStore((s) => s.selectedRowIndex);
  const setHoveredRow = useUIStore((s) => s.setHoveredRow);
  const setSelectedRow = useUIStore((s) => s.setSelectedRow);

  // Map a BOM row index to its dimension-ladder segment (if it's a base cabinet
  // whose width matches one of the extracted segment widths, in order).
  const rowToSegment = mapRowsToSegments(rows, segments);

  const activeRowIndex =
    selectedRowIndex !== null ? selectedRowIndex : hoveredRowIndex;
  const activeSegment =
    activeRowIndex !== null ? rowToSegment.get(activeRowIndex) ?? null : null;
  const isSelected = selectedRowIndex !== null;

  const haveImageDims = imageWidthPx > 0 && imageHeightPx > 0;

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="h-9 px-3 flex items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)]">
        <div className="flex items-center gap-2 text-[12px]">
          <span className="text-[var(--color-text-muted)]">Page</span>
          <span className="font-mono font-medium text-[var(--color-text)]">
            {pageNumber}
          </span>
          <span className="text-[var(--color-text-subtle)]">·</span>
          <span className="text-[var(--color-text-muted)]">{variantLabel}</span>
          {segments.length > 0 && (
            <>
              <span className="text-[var(--color-text-subtle)]">·</span>
              <span className="text-[10px] text-[var(--color-text-subtle)]">
                {segments.length} segments mapped
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}
            aria-label="Zoom out"
          >
            <ZoomOut size={12} />
          </Button>
          <span className="text-[11px] font-mono text-[var(--color-text-muted)] px-1.5 tabular-nums w-10 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
            aria-label="Zoom in"
          >
            <ZoomIn size={12} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom(1)}
            aria-label="Fit"
          >
            <Maximize2 size={12} />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 flex items-start justify-center bg-[var(--color-surface-2)]">
        <div
          className="relative inline-block bg-white shadow-sm border border-[var(--color-border)]"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top center",
            transition: "transform 0.15s ease",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgUrl}
            alt={`Blueprint page ${pageNumber}`}
            className="block max-w-full"
            draggable={false}
          />

          {haveImageDims && activeSegment && (
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none"
              viewBox={`0 0 ${imageWidthPx} ${imageHeightPx}`}
              preserveAspectRatio="xMidYMid meet"
            >
              <rect
                x={activeSegment.x0_px}
                y={activeSegment.y0_px}
                width={activeSegment.x1_px - activeSegment.x0_px}
                height={activeSegment.y1_px - activeSegment.y0_px}
                fill={
                  isSelected
                    ? "rgba(37, 99, 235, 0.32)"
                    : "rgba(37, 99, 235, 0.20)"
                }
                stroke="rgb(37, 99, 235)"
                strokeWidth={isSelected ? 8 : 5}
                rx={6}
              />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Map BOM rows to dimension-ladder segments.
 *
 * The PDF dimension ladder contains the kitchen-run segments left-to-right
 * (e.g. [20, 280, 600, 400, 800, 20] for 26A). The BOM has rows for every
 * cabinet/panel/trim. We want hovering "row 9" (찬넬렌지밑장 = 600mm range)
 * to highlight the 600mm segment.
 *
 * Strategy:
 * 1. Filter BOM rows to base cabinets only (C/CR/CS/CD2/CD3 etc).
 * 2. They appear left-to-right in the same order as the inner ladder
 *    segments (excluding the leading/trailing 20mm fillers).
 * 3. Match by order; verify by width_mm.
 */
function mapRowsToSegments(
  rows: CabinetRow[],
  segments: Segment[]
): Map<number, Segment> {
  const result = new Map<number, Segment>();
  if (segments.length < 3) return result;

  // Inner segments — skip the 20mm fillers at start and end of the ladder
  // (these are typically narrow end panels, not base cabinets).
  const inner = segments.filter((s) => s.width_mm > 30);
  if (inner.length === 0) return result;

  // Filter base-cabinet rows in BOM order
  const baseRows = rows.filter(
    (r) =>
      r.category === "목대" &&
      r.width_mm !== null &&
      isBaseCabinetCode(r.code)
  );

  // Match by index, verify by width
  for (let i = 0; i < Math.min(baseRows.length, inner.length); i++) {
    const row = baseRows[i];
    const seg = inner[i];
    // Allow ±5mm tolerance for sub-millimeter rounding (e.g. 601 vs 600)
    if (
      row.width_mm !== null &&
      Math.abs(row.width_mm - seg.width_mm) <= 5
    ) {
      result.set(row.index, seg);
    } else {
      // Fall back to width match anywhere in the inner segments
      const exact = inner.find((s) => s.width_mm === row.width_mm);
      if (exact) result.set(row.index, exact);
    }
  }

  return result;
}

function isBaseCabinetCode(code: string): boolean {
  return ["B", "BR", "BS", "BD2", "BD3", "C", "CR", "CS", "CD2", "CD3"].includes(
    code
  );
}
