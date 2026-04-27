"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, AlertCircle } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { formatKRW } from "@/lib/utils";
import type { Validation } from "@/lib/types";

interface Props {
  projectId: string;
  variantCode: string;
  validations: Validation[];
  units: number;
  isApproved: boolean;
}

export function ValidationsBar({
  projectId,
  variantCode,
  validations,
  units,
  isApproved,
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

  // Mock cost (in real app from server)
  const costPerUnit = 1_847_200;
  const total_cost = costPerUnit * units;

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
        <span className="text-[var(--color-text-subtle)]">·</span>
        <span className="text-[var(--color-text-muted)]">
          Est. <span className="font-medium text-[var(--color-text)]">{formatKRW(total_cost)}</span>{" "}
          ({units} × {formatKRW(costPerUnit)})
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" size="md">
          Open in Excel
        </Button>
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
