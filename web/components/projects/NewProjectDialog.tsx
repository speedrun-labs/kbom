"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8765";

export function NewProjectDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [developer, setDeveloper] = useState("LH");
  const router = useRouter();
  const qc = useQueryClient();

  const create = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("Choose a PDF first.");
      const fd = new FormData();
      fd.append("name", name || file.name.replace(/\.pdf$/i, ""));
      fd.append("developer", developer);
      fd.append("pdf", file);
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      return res.json() as Promise<{ id: string }>;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      onOpenChange(false);
      setFile(null);
      setName("");
      router.push(`/projects/${data.id}`);
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New project</DialogTitle>
          <DialogDescription>
            Upload a kitchen blueprint PDF. The pipeline will detect unit-type
            variants and extract a BOM for each.
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-3">
          <FilePicker file={file} onFile={setFile} />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Project name">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={file?.name.replace(/\.pdf$/i, "") ?? "e.g. 화성태안3 A2BL"}
                className="h-8 w-full rounded border border-[var(--color-border)] bg-white px-2.5 text-[13px] focus:border-[var(--color-brand-500)] focus:outline-none"
              />
            </Field>
            <Field label="Developer">
              <select
                value={developer}
                onChange={(e) => setDeveloper(e.target.value)}
                className="h-8 w-full rounded border border-[var(--color-border)] bg-white px-2.5 text-[13px] focus:border-[var(--color-brand-500)] focus:outline-none"
              >
                <option value="LH">LH</option>
                <option value="SH">SH (Seoul)</option>
                <option value="GH">GH (Gyeonggi)</option>
                <option value="Private">Private</option>
              </select>
            </Field>
          </div>
          {create.isError && (
            <p className="text-[12px] text-[var(--color-danger-fg)]">
              {(create.error as Error).message}
            </p>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!file || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? (
              <>
                <Loader2 size={12} className="animate-spin" />
                Extracting…
              </>
            ) : (
              <>Create project →</>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-medium text-[var(--color-text-muted)] mb-1">
        {label}
      </span>
      {children}
    </label>
  );
}

function FilePicker({
  file,
  onFile,
}: {
  file: File | null;
  onFile: (f: File | null) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  return (
    <label
      className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-lg cursor-pointer transition-colors px-6 py-8 text-center ${
        isDragging
          ? "border-[var(--color-brand-500)] bg-[var(--color-brand-50)]"
          : file
          ? "border-[var(--color-success-fg)] bg-[var(--color-success-bg)]"
          : "border-[var(--color-border)] hover:border-slate-300 hover:bg-[var(--color-surface-2)]"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const f = e.dataTransfer.files?.[0];
        if (f && f.type === "application/pdf") onFile(f);
      }}
    >
      <input
        type="file"
        accept="application/pdf"
        className="absolute inset-0 opacity-0 cursor-pointer"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
      <Upload
        size={20}
        className={
          file
            ? "text-[var(--color-success-fg)]"
            : "text-[var(--color-text-subtle)]"
        }
      />
      <p className="text-[13px] mt-2 font-medium text-[var(--color-text)]">
        {file ? file.name : "Drop PDF here or click to choose"}
      </p>
      <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">
        {file
          ? `${(file.size / 1024 / 1024).toFixed(1)} MB`
          : "Vector PDFs from CAD work best"}
      </p>
    </label>
  );
}
