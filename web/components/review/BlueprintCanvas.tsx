"use client";

import { useState } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function BlueprintCanvas({
  projectId,
  pageNumber,
  variantLabel,
}: {
  projectId: string;
  pageNumber: number;
  variantLabel: string;
}) {
  const [zoom, setZoom] = useState(1);
  const imgUrl = api.blueprintImageUrl(projectId, pageNumber);

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Toolbar */}
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
            aria-label="Fit to view"
          >
            <Maximize2 size={12} />
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-auto p-4 flex items-start justify-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imgUrl}
          alt={`Blueprint page ${pageNumber}`}
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top center",
            transition: "transform 0.15s ease",
          }}
          className="max-w-full shadow-sm border border-[var(--color-border)] bg-white"
        />
      </div>
    </div>
  );
}
