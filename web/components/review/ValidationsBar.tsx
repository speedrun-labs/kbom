"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, AlertCircle, Download } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { formatKRW } from "@/lib/utils";
import type { Validation } from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8765";

interface Props {
  projectId: string;
  variantCode: string;
  validations: Validation[];
  units: number;
  isApproved: boolean;
  costPerUnit: number | null;
  costTotal: number | null;
}

export function ValidationsBar({
  projectId,
  variantCode,
  validations,
  units,
  isApproved,
  costPerUnit,
  costTotal,
}: Props) {
  const passed = validations.filter((v) => v.passed).length;
  const total = validations.length;
  const allPass = passed === total;

  const qc = useQueryClient();
  const approve = useMutation({
    mutationFn: () => api.approveVariant(projectId, variantCode, !isApproved),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({
        queryKey: ["variant", projectId, variantCode],
      });
    },
  });

  return (
    <div className="h-12 flex items-center justify-between px-4 border-t border-[var(--color-border)] bg-white">
      <div className="flex items-center gap-4 text-[12px]">
        <div className="flex items-center gap-1.5">
          {allPass ? (
            <Check size={13} className="text-[var(--color-success-fg)]" />
          ) : (
            <AlertCircle size={13} className="text-[var(--color-warning-fg)]" />
          )}
          <span
            className={
              allPass
                ? "text-[var(--color-success-fg)] font-medium"
                : "text-[var(--color-warning-fg)] font-medium"
            }
          >
            {passed}/{total} validations
          </span>
        </div>
        {costPerUnit !== null && costTotal !== null && (
          <>
            <span className="text-[var(--color-text-subtle)]">·</span>
            <span className="text-[var(--color-text-muted)]">
              Est.{" "}
              <span className="font-medium text-[var(--color-text)]">
                {formatKRW(costTotal)}
              </span>{" "}
              <span className="text-[var(--color-text-subtle)]">
                ({units} × {formatKRW(costPerUnit)})
              </span>
            </span>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <a
          href={`${API_BASE}/api/projects/${projectId}/download.xlsx`}
          download
        >
          <Button variant="secondary" size="md">
            <Download size={12} />
            Download Excel
          </Button>
        </a>
        <Button
          variant={isApproved ? "secondary" : "primary"}
          size="md"
          onClick={() => approve.mutate()}
          disabled={approve.isPending}
        >
          {isApproved ? "✓ Approved (undo)" : "Approve variant ✓"}
        </Button>
      </div>
    </div>
  );
}
