import type {
  ProjectDetail,
  ProjectSummary,
  VariantDetail,
  CabinetRow,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8765";

async function jsonFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => jsonFetch<ProjectSummary[]>("/api/projects"),

  getProject: (id: string) =>
    jsonFetch<ProjectDetail>(`/api/projects/${id}`),

  createSample: () =>
    jsonFetch<ProjectDetail>("/api/projects/sample", { method: "POST" }),

  getVariant: (projectId: string, code: string) =>
    jsonFetch<VariantDetail>(
      `/api/projects/${projectId}/variants/${code}`
    ),

  approveVariant: (projectId: string, code: string, approved = true) =>
    jsonFetch<{ approved: boolean; project_status: string }>(
      `/api/projects/${projectId}/variants/${code}/approve`,
      {
        method: "POST",
        body: JSON.stringify({ approved }),
      }
    ),

  updateRow: (
    projectId: string,
    code: string,
    rowIndex: number,
    update: Partial<Pick<CabinetRow, "width_mm" | "depth_mm" | "height_mm" | "code" | "name">>
  ) =>
    jsonFetch<CabinetRow>(
      `/api/projects/${projectId}/variants/${code}/rows/${rowIndex}`,
      {
        method: "PATCH",
        body: JSON.stringify(update),
      }
    ),

  blueprintImageUrl: (projectId: string, page: number) =>
    `${API_BASE}/api/projects/${projectId}/blueprint/${page}.png`,
};
