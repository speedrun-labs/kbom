"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock,
  CircleDot,
  ArrowUpRight,
  Sparkles,
  Plus,
} from "lucide-react";

import { api } from "@/lib/api";
import { TopBar } from "@/components/layout/TopBar";
import { LeftRail } from "@/components/layout/LeftRail";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { NewProjectDialog } from "@/components/projects/NewProjectDialog";
import type { ProjectSummary } from "@/lib/types";

export default function HomePage() {
  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  const qc = useQueryClient();
  const createSample = useMutation({
    mutationFn: api.createSample,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });

  const [newProjectOpen, setNewProjectOpen] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-[var(--color-bg)]">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        <LeftRail />
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-8 py-8">
            <div className="flex items-end justify-between mb-8">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-[var(--color-text)]">
                  Projects
                </h1>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">
                  Active and recent kitchen extractions
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => createSample.mutate()}
                  disabled={createSample.isPending}
                  variant="secondary"
                >
                  <Sparkles size={14} />
                  {createSample.isPending ? "Creating…" : "Use sample"}
                </Button>
                <Button
                  variant="primary"
                  onClick={() => setNewProjectOpen(true)}
                >
                  <Plus size={14} />
                  New project
                </Button>
              </div>
            </div>

            {projects.isLoading && (
              <div className="text-sm text-[var(--color-text-muted)] py-8 text-center">
                Loading…
              </div>
            )}

            {projects.data?.length === 0 && (
              <EmptyState
                onSample={() => createSample.mutate()}
                loading={createSample.isPending}
                onUpload={() => setNewProjectOpen(true)}
              />
            )}

            {(projects.data?.length ?? 0) > 0 && (
              <div className="space-y-px rounded-lg overflow-hidden border border-[var(--color-border)] bg-white">
                {projects.data!.map((p) => (
                  <ProjectRow key={p.id} project={p} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      <NewProjectDialog
        open={newProjectOpen}
        onOpenChange={setNewProjectOpen}
      />
    </div>
  );
}

function ProjectRow({ project }: { project: ProjectSummary }) {
  const status = statusMeta(project.status);
  return (
    <Link
      href={`/projects/${project.id}`}
      className="group flex items-center gap-4 px-5 py-4 hover:bg-[var(--color-surface-2)] transition-colors border-b border-[var(--color-border-soft)] last:border-b-0"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-[14px] font-medium text-[var(--color-text)] truncate">
            {project.name}
          </h3>
          <Badge tone="neutral" size="sm">
            {project.developer}
          </Badge>
        </div>
        <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">
          {project.variants_count} variants · {project.units_total} units · created{" "}
          {project.created_at.slice(0, 10)}
        </p>
      </div>

      <div className="flex items-center gap-1.5 text-[12px] text-[var(--color-text-muted)] tabular-nums">
        <span>{project.approved_variants}</span>
        <span className="text-[var(--color-text-subtle)]">/</span>
        <span>{project.variants_count}</span>
        <span className="text-[var(--color-text-subtle)]">approved</span>
      </div>

      <div className="flex items-center gap-1.5">
        <status.Icon size={12} className={status.colorClass} />
        <span className={`text-[12px] font-medium ${status.colorClass}`}>
          {project.status}
        </span>
      </div>

      <ArrowUpRight
        size={14}
        className="text-[var(--color-text-subtle)] opacity-0 group-hover:opacity-100 transition-opacity"
      />
    </Link>
  );
}

function statusMeta(status: string) {
  if (status === "Approved") {
    return { Icon: CheckCircle2, colorClass: "text-[var(--color-success-fg)]" };
  }
  if (status === "In review" || status === "Awaiting review") {
    return { Icon: Clock, colorClass: "text-[var(--color-warning-fg)]" };
  }
  return { Icon: CircleDot, colorClass: "text-[var(--color-text-muted)]" };
}

function EmptyState({
  onSample,
  loading,
  onUpload,
}: {
  onSample: () => void;
  loading: boolean;
  onUpload: () => void;
}) {
  return (
    <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-white p-12 text-center">
      <div className="text-3xl mb-2">📐</div>
      <h3 className="text-[15px] font-semibold text-[var(--color-text)]">
        No projects yet
      </h3>
      <p className="text-[13px] text-[var(--color-text-muted)] mt-1 mb-5 max-w-sm mx-auto">
        Upload your first blueprint, or kick the tires with the bundled NEFS
        sample (<code className="font-mono text-[12px]">화성태안3 A2BL</code>).
      </p>
      <div className="flex items-center justify-center gap-2">
        <Button variant="primary" onClick={onSample} disabled={loading}>
          <Sparkles size={14} />
          {loading ? "Creating sample…" : "Try with sample"}
        </Button>
        <Button variant="secondary" onClick={onUpload}>
          <Plus size={14} />
          Upload PDF
        </Button>
      </div>
    </div>
  );
}
