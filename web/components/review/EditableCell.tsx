"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  projectId: string;
  variantCode: string;
  rowIndex: number;
  field: "width_mm" | "depth_mm" | "height_mm";
  value: number | null;
}

export function EditableCell({
  projectId,
  variantCode,
  rowIndex,
  field,
  value,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value?.toString() ?? "");
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  useEffect(() => {
    if (editing) {
      setDraft(value?.toString() ?? "");
      requestAnimationFrame(() => inputRef.current?.select());
    }
  }, [editing, value]);

  const update = useMutation({
    mutationFn: (newValue: number) =>
      api.updateRow(projectId, variantCode, rowIndex, { [field]: newValue }),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["variant", projectId, variantCode],
      });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });

  const commit = () => {
    setEditing(false);
    const n = parseInt(draft, 10);
    if (!isNaN(n) && n !== value) {
      update.mutate(n);
    }
  };

  const cancel = () => {
    setEditing(false);
    setDraft(value?.toString() ?? "");
  };

  if (value === null) return <span className="text-[var(--color-text-subtle)]">—</span>;

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="number"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") cancel();
        }}
        onClick={(e) => e.stopPropagation()}
        className="w-14 h-5 px-1 text-right font-mono text-[12px] bg-white border border-[var(--color-brand-500)] rounded focus:outline-none tabular-nums"
      />
    );
  }

  return (
    <span
      onClick={(e) => {
        e.stopPropagation();
        setEditing(true);
      }}
      className={cn(
        "inline-block px-1 py-0 rounded font-mono cursor-pointer hover:bg-[var(--color-surface-2)] tabular-nums",
        update.isPending && "opacity-50"
      )}
    >
      {value}
    </span>
  );
}
