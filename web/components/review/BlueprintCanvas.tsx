"use client";

import { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/lib/store";
import type { CabinetRow } from "@/lib/types";

interface Props {
  projectId: string;
  pageNumber: number;
  variantLabel: string;
  rows: CabinetRow[];
}

export function BlueprintCanvas({
  projectId,
  pageNumber,
  variantLabel,
  rows,
}: Props) {
  const [zoom, setZoom] = useState(1);
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  const imgUrl = api.blueprintImageUrl(projectId, pageNumber);

  const hoveredRowIndex = useUIStore((s) => s.hoveredRowIndex);
  const selectedRowIndex = useUIStore((s) => s.selectedRowIndex);
  const setHoveredRow = useUIStore((s) => s.setHoveredRow);
  const setSelectedRow = useUIStore((s) => s.setSelectedRow);

  // Compute approximate segment positions on the rendered PDF.
  // The plan view sits roughly in the upper-left quadrant (x: 0.16-0.45 of page width,
  // y: 0.42-0.70 of page height for the cabinet run line). We position SVG rectangles
  // that align to base-cabinet rows by their dimensional widths.
  const segments = computeSegments(rows);

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
            onLoad={(e) => {
              const img = e.currentTarget;
              setImgSize({ w: img.naturalWidth, h: img.naturalHeight });
            }}
            className="block max-w-full"
            draggable={false}
          />

          {imgSize && (
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none"
              viewBox={`0 0 ${imgSize.w} ${imgSize.h}`}
              preserveAspectRatio="xMidYMid meet"
            >
              {segments
                .filter(
                  (s) =>
                    s.rowIndex === hoveredRowIndex ||
                    s.rowIndex === selectedRowIndex
                )
                .map((s) => {
                  const isSelected = s.rowIndex === selectedRowIndex;
                  return (
                    <g key={`${s.row}-${s.kind}`}>
                      <rect
                        x={s.x * imgSize.w}
                        y={s.y * imgSize.h}
                        width={s.w * imgSize.w}
                        height={s.h * imgSize.h}
                        fill={
                          isSelected
                            ? "rgba(37, 99, 235, 0.30)"
                            : "rgba(37, 99, 235, 0.20)"
                        }
                        stroke="rgb(37, 99, 235)"
                        strokeWidth={isSelected ? 5 : 3}
                        rx={4}
                        className="pointer-events-none"
                      />
                    </g>
                  );
                })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}

interface Segment {
  row: number;
  rowIndex: number;
  kind: "base" | "wall";
  // Normalized 0..1 coordinates relative to image
  x: number;
  y: number;
  w: number;
  h: number;
}

function computeSegments(rows: CabinetRow[]): Segment[] {
  // Plan view location on the LH detail pages (landscape A3 ~2482x1755).
  // The kitchen plan view (평면도) sits in the upper-left of the page;
  // within it, the cabinet outline is a thin horizontal band.
  //
  // Coordinates are normalized 0..1 of the page image. Approximate — future
  // Path B (DXF) adapter will give pixel-exact positions. Tuned for the
  // bundled 26A sample.
  const PLAN_X0 = 0.085;
  const PLAN_X1 = 0.31;
  const PLAN_RUN_W = PLAN_X1 - PLAN_X0;

  // Base cabinet outline — the lower row of the plan rectangle
  const BASE_Y0 = 0.205;
  const BASE_Y1 = 0.235;

  // Wall cabinet outline — the upper row of the plan rectangle (dashed in
  // the actual drawing, since it's a top-down view of overhead cabinets)
  const WALL_Y0 = 0.135;
  const WALL_Y1 = 0.165;

  // Group dimensional rows by category (목대) and infer their position in the run.
  // We treat panels (WP/BP/BI/FA/PL) as zero-width markers — they don't sit on the
  // run line. Cabinets (W, B, C, CR, CD3, CS …) consume horizontal space.
  const baseCabinetRows: CabinetRow[] = [];
  const wallCabinetRows: CabinetRow[] = [];

  for (const row of rows) {
    if (row.category !== "목대" || row.width_mm === null) continue;
    if (isPanelOrTrim(row.code)) continue;
    if (isWallCabinet(row.code)) {
      wallCabinetRows.push(row);
    } else if (isBaseCabinet(row.code)) {
      baseCabinetRows.push(row);
    }
  }

  const segments: Segment[] = [];

  function layout(
    cabinets: CabinetRow[],
    y0: number,
    y1: number,
    kind: "base" | "wall"
  ) {
    const totalMM = cabinets.reduce((s, r) => s + (r.width_mm ?? 0), 0);
    if (totalMM === 0) return;
    let cursor = 0;
    for (const r of cabinets) {
      const width_norm = ((r.width_mm ?? 0) / totalMM) * PLAN_RUN_W;
      segments.push({
        row: r.index,
        rowIndex: r.index,
        kind,
        x: PLAN_X0 + cursor,
        y: y0,
        w: width_norm,
        h: y1 - y0,
      });
      cursor += width_norm;
    }
  }

  layout(baseCabinetRows, BASE_Y0, BASE_Y1, "base");
  layout(wallCabinetRows, WALL_Y0, WALL_Y1, "wall");

  return segments;
}

function isPanelOrTrim(code: string): boolean {
  return ["WP", "BP", "BI", "FA", "PL"].includes(code);
}
function isWallCabinet(code: string): boolean {
  return code === "W" || code === "WH" || code === "WE" || code === "WC";
}
function isBaseCabinet(code: string): boolean {
  return ["B", "BR", "BS", "BD2", "BD3", "C", "CR", "CS", "CD2", "CD3"].includes(code);
}
