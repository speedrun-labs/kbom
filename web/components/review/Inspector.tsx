"use client";

import { X, FileText, User, Brain } from "lucide-react";

import type { CabinetRow } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/lib/store";

interface Props {
  row: CabinetRow | null;
}

export function Inspector({ row }: Props) {
  const setInspectorOpen = useUIStore((s) => s.setInspectorOpen);

  if (!row) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-6 text-center bg-white">
        <Brain
          size={32}
          className="text-[var(--color-text-subtle)] mb-3"
          strokeWidth={1.2}
        />
        <p className="text-[13px] font-medium text-[var(--color-text)]">
          Cell inspector
        </p>
        <p className="text-[12px] text-[var(--color-text-muted)] mt-1 leading-relaxed max-w-[180px]">
          Click any row to see its formula, AI confidence, rule citations, and
          edit history.
        </p>
      </div>
    );
  }

  const dim =
    row.width_mm !== null
      ? `${row.width_mm} × ${row.depth_mm ?? "—"} × ${row.height_mm ?? "—"} mm`
      : "—";

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="h-9 px-3 flex items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)]">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-[var(--color-text-muted)]">
          Inspector
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setInspectorOpen(false)}
        >
          <X size={12} />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Title */}
        <div>
          <div className="flex items-center gap-2">
            <span
              className={
                row.category === "목대"
                  ? "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#D1FAE5] text-[#059669]"
                  : "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#EDE9FE] text-[#7C3AED]"
              }
            >
              {row.category}
            </span>
            {row.code && (
              <code className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--color-surface-2)] text-[var(--color-text-muted)]">
                {row.code}
              </code>
            )}
          </div>
          <h3 className="text-[15px] font-semibold mt-1.5 text-[var(--color-text)]">
            {row.name}
          </h3>
          <p className="text-[12px] font-mono text-[var(--color-text-muted)] mt-0.5 tabular-nums">
            {dim}
          </p>
        </div>

        <hr className="border-[var(--color-border-soft)]" />

        {/* From Excel section */}
        <Section icon={FileText} title="From Excel file">
          <Field label="Sheet">
            <code className="text-[11px]">장등록(규격,수량,옵션)</code>
          </Field>
          <Field label="Row">
            <code className="text-[11px]">{row.index + 4}</code>
          </Field>
          <Field label="Type label">
            <code className="text-[11px]">{row.type_label}</code>
          </Field>
        </Section>

        <hr className="border-[var(--color-border-soft)]" />

        {/* From Platform section */}
        <Section icon={User} title="Provenance">
          <Field label="Source">
            <span className="text-[12px] capitalize">
              {row.source.replace("_", " ")}
            </span>
          </Field>
          {row.source === "vision" && (
            <Field label="AI confidence">
              <span className="text-[12px] font-mono tabular-nums">
                {(row.confidence * 100).toFixed(0)}%
              </span>
            </Field>
          )}
          {row.rule_citation && (
            <>
              <Field label="Rule">
                <code className="text-[11px] px-1.5 py-0.5 rounded bg-[var(--color-rule-bg)] text-[var(--color-rule-fg)]">
                  {row.rule_citation.rule_id}
                </code>
              </Field>
              <Field label="Description" stacked>
                <p className="text-[12px] text-[var(--color-text-muted)] leading-relaxed mt-1">
                  {row.rule_citation.description}
                </p>
              </Field>
              <Field label="Source" stacked>
                <p className="text-[11px] text-[var(--color-text-muted)] mt-1">
                  {row.rule_citation.document}
                  {row.rule_citation.section_code && (
                    <>
                      {" · "}
                      <code className="text-[11px]">
                        {row.rule_citation.section_code}
                      </code>
                    </>
                  )}
                  {row.rule_citation.page && (
                    <>
                      {" · page "}
                      <span className="font-mono">{row.rule_citation.page}</span>
                    </>
                  )}
                </p>
              </Field>
            </>
          )}
        </Section>
      </div>

      <div className="px-4 py-3 border-t border-[var(--color-border-soft)]">
        <Button variant="secondary" size="sm" className="w-full">
          Open in Excel
        </Button>
      </div>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <Icon size={12} className="text-[var(--color-text-subtle)]" />
        <span className="text-[10px] font-semibold tracking-wider uppercase text-[var(--color-text-subtle)]">
          {title}
        </span>
      </div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Field({
  label,
  stacked,
  children,
}: {
  label: string;
  stacked?: boolean;
  children: React.ReactNode;
}) {
  if (stacked) {
    return (
      <div>
        <span className="text-[11px] text-[var(--color-text-subtle)]">
          {label}
        </span>
        {children}
      </div>
    );
  }
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-[11px] text-[var(--color-text-subtle)]">{label}</span>
      <div className="text-right">{children}</div>
    </div>
  );
}
