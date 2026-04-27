"use client";

import { Command } from "cmdk";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { FileText, Plus, Sparkles, Layers } from "lucide-react";

import { api } from "@/lib/api";

import "./CommandPalette.css";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const router = useRouter();

  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  const qc = useQueryClient();
  const createSample = useMutation({
    mutationFn: api.createSample,
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      router.push(`/projects/${project.id}`);
    },
  });

  // Toggle on ⌘K / Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      className="cmdk-dialog"
    >
      <div className="cmdk-shell">
        <Command.Input
          value={search}
          onValueChange={setSearch}
          placeholder="Search projects, actions…"
          className="cmdk-input"
        />
        <Command.List className="cmdk-list">
          <Command.Empty className="cmdk-empty">No results.</Command.Empty>

          <Command.Group heading="Actions" className="cmdk-group">
            <Command.Item
              onSelect={() => {
                setOpen(false);
                createSample.mutate();
              }}
              className="cmdk-item"
            >
              <Sparkles size={14} />
              <span>Create sample project</span>
              <span className="cmdk-shortcut">demo</span>
            </Command.Item>
            <Command.Item
              onSelect={() => {
                setOpen(false);
                router.push("/");
              }}
              className="cmdk-item"
            >
              <Layers size={14} />
              <span>Go to projects</span>
            </Command.Item>
          </Command.Group>

          {(projects.data?.length ?? 0) > 0 && (
            <Command.Group heading="Open project" className="cmdk-group">
              {projects.data!.map((p) => (
                <Command.Item
                  key={p.id}
                  value={`${p.name} ${p.developer}`}
                  onSelect={() => {
                    setOpen(false);
                    router.push(`/projects/${p.id}`);
                  }}
                  className="cmdk-item"
                >
                  <FileText size={14} />
                  <span>{p.name}</span>
                  <span className="cmdk-shortcut">{p.developer}</span>
                </Command.Item>
              ))}
            </Command.Group>
          )}
        </Command.List>
      </div>
    </Command.Dialog>
  );
}
