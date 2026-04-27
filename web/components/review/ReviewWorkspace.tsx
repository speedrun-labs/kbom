"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useUIStore } from "@/lib/store";
import { BlueprintCanvas } from "./BlueprintCanvas";
import { BomGrid } from "./BomGrid";
import { Inspector } from "./Inspector";
import { ValidationsBar } from "./ValidationsBar";
import { VariantTabs } from "./VariantTabs";
import type { ProjectDetail } from "@/lib/types";

interface Props {
  project: ProjectDetail;
  activeVariantCode: string;
  onChangeVariant: (code: string) => void;
}

export function ReviewWorkspace({
  project,
  activeVariantCode,
  onChangeVariant,
}: Props) {
  const variantQuery = useQuery({
    queryKey: ["variant", project.id, activeVariantCode],
    queryFn: () => api.getVariant(project.id, activeVariantCode),
  });

  const selectedRowIndex = useUIStore((s) => s.selectedRowIndex);
  const inspectorOpen = useUIStore((s) => s.inspectorOpen);
  const setSelectedRow = useUIStore((s) => s.setSelectedRow);

  // Reset selection when variant changes
  useEffect(() => {
    setSelectedRow(null);
  }, [activeVariantCode, setSelectedRow]);

  const variant = variantQuery.data;
  const selectedRow =
    variant && selectedRowIndex !== null
      ? variant.rows[selectedRowIndex] ?? null
      : null;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <VariantTabs
        variants={project.variants}
        activeCode={activeVariantCode}
        onSelect={onChangeVariant}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Blueprint pane */}
        <div className="w-[44%] border-r border-[var(--color-border)] flex flex-col">
          {variant && (
            <BlueprintCanvas
              projectId={project.id}
              pageNumber={variant.page_number}
              variantLabel={variant.label}
            />
          )}
        </div>

        {/* BOM grid pane */}
        <div className="flex-1 flex flex-col">
          {variant && (
            <BomGrid
              projectId={project.id}
              variantCode={activeVariantCode}
              rows={variant.rows}
            />
          )}
        </div>

        {/* Inspector pane (collapses if closed) */}
        <div
          className={
            inspectorOpen
              ? "w-[300px] shrink-0 border-l border-[var(--color-border)] transition-all"
              : "w-0 overflow-hidden border-l border-transparent"
          }
        >
          {inspectorOpen && <Inspector row={selectedRow} />}
        </div>
      </div>

      {variant && (
        <ValidationsBar
          projectId={project.id}
          variantCode={activeVariantCode}
          validations={variant.validations}
          units={variant.units}
          isApproved={variant.is_approved}
        />
      )}
    </div>
  );
}
