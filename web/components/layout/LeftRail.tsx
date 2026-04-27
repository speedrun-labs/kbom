"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronRight,
  Folder,
  Inbox,
  Archive,
  Plus,
} from "lucide-react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function LeftRail() {
  const params = useParams<{ id?: string }>();
  const pathname = usePathname();
  const currentProjectId = params?.id;

  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  return (
    <aside className="w-56 shrink-0 border-r border-[var(--color-border)] bg-white flex flex-col">
      <div className="px-3 py-2.5 flex items-center justify-between">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-[var(--color-text-subtle)]">
          Workspace
        </span>
      </div>

      <nav className="px-2 space-y-0.5 mb-3">
        <NavLink href="/" icon={Inbox} label="All projects" active={pathname === "/"} />
        <NavLink href="/" icon={Folder} label="Drafts" />
        <NavLink href="/" icon={Archive} label="Archive" />
      </nav>

      <div className="px-3 py-2 flex items-center justify-between">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-[var(--color-text-subtle)]">
          Active
        </span>
        <button className="h-5 w-5 inline-flex items-center justify-center rounded text-[var(--color-text-subtle)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text-muted)]">
          <Plus size={12} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {projects.data?.length === 0 && (
          <div className="text-xs text-[var(--color-text-subtle)] px-3 py-3">
            No projects yet
          </div>
        )}
        {projects.data?.map((p) => {
          const isActive = p.id === currentProjectId;
          return (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className={cn(
                "block px-3 py-2 rounded text-xs leading-tight transition-colors",
                isActive
                  ? "bg-[var(--color-brand-50)] text-[var(--color-brand-700)]"
                  : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]"
              )}
            >
              <div className="flex items-center gap-1.5">
                <ChevronRight size={10} className="opacity-50" />
                <span className="truncate flex-1 font-medium text-[13px]">
                  {p.name}
                </span>
              </div>
              <div className="ml-3.5 mt-0.5 text-[11px] text-[var(--color-text-subtle)]">
                {p.developer} · {p.approved_variants}/{p.variants_count} ✓
              </div>
            </Link>
          );
        })}
      </div>

      <div className="px-3 py-2 border-t border-[var(--color-border-soft)]">
        <p className="text-[10px] text-[var(--color-text-subtle)]">
          KBOM 0.2 · Stage 1 prototype
        </p>
      </div>
    </aside>
  );
}

function NavLink({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  active?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 px-2.5 py-1.5 rounded text-[13px] transition-colors",
        active
          ? "bg-[var(--color-surface-2)] text-[var(--color-text)] font-medium"
          : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]"
      )}
    >
      <Icon size={14} />
      <span>{label}</span>
    </Link>
  );
}
