import type { CabinetRow } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

export function ConfidencePill({ row }: { row: CabinetRow }) {
  if (row.source === "rule") {
    return (
      <Badge tone="rule" size="sm">
        ⚙ rule
      </Badge>
    );
  }
  if (row.source === "catalog") {
    return (
      <Badge tone="rule" size="sm">
        ★ catalog
      </Badge>
    );
  }
  if (row.source === "human") {
    return (
      <Badge tone="info" size="sm">
        ✎ edited
      </Badge>
    );
  }

  const pct = Math.round(row.confidence * 100);
  if (row.source === "spec_table") {
    return (
      <Badge tone="neutral" size="sm">
        spec {pct}
      </Badge>
    );
  }
  if (pct >= 85) {
    return (
      <Badge tone="success" size="sm">
        ●{pct}
      </Badge>
    );
  }
  if (pct >= 60) {
    return (
      <Badge tone="warning" size="sm">
        ⚠{pct}
      </Badge>
    );
  }
  return (
    <Badge tone="danger" size="sm">
      ✗{pct}
    </Badge>
  );
}
