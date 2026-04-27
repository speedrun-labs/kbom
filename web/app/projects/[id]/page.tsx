"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { TopBar } from "@/components/layout/TopBar";
import { LeftRail } from "@/components/layout/LeftRail";
import { ReviewWorkspace } from "@/components/review/ReviewWorkspace";

export default function ProjectPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
  });

  const [activeVariantCode, setActiveVariantCode] = useState<string | null>(
    null
  );

  useEffect(() => {
    if (project.data && !activeVariantCode) {
      setActiveVariantCode(project.data.variants[0]?.code ?? null);
    }
  }, [project.data, activeVariantCode]);

  return (
    <div className="h-screen flex flex-col bg-[var(--color-bg)]">
      <TopBar projectName={project.data?.name} />
      <div className="flex-1 flex overflow-hidden">
        <LeftRail />
        {project.isLoading && (
          <div className="flex-1 flex items-center justify-center text-sm text-[var(--color-text-muted)]">
            Loading project…
          </div>
        )}
        {project.data && activeVariantCode && (
          <ReviewWorkspace
            project={project.data}
            activeVariantCode={activeVariantCode}
            onChangeVariant={setActiveVariantCode}
          />
        )}
      </div>
    </div>
  );
}
