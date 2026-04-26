import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Plug2 } from "lucide-react";
import { Link } from "react-router-dom";

import {
  BrutalistTable,
  BrutalistTableBody,
  BrutalistTableCell,
  BrutalistTableRow,
  CollapsibleSection,
  StatusBadge,
  type StatusVariant,
} from "@/components/torale";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn, getErrorMessage } from "@/lib/utils";
import api from "@/lib/api";
// Mirror of backend ConnectionStatus StrEnum (backend/src/torale/connectors/client.py); keep in sync.
import type { ConnectionStatus, UserConnection } from "@/types";

/**
 * Task creation/edit connector picker.
 *
 * Collapsed-by-default section that lets users attach user-level connectors to
 * a task. Selection is a string[] of toolkit slugs. See design memo §4, §10.1.
 *
 * Behavior:
 * - Empty state: prompt to connect, don't block task save.
 * - EXPIRED rows: visually flagged, selectable (preserve user intent on edit).
 * - >3 selected: soft advisory above rows.
 */

const ADVISORY_THRESHOLD = 3;

interface ConnectorPickerSectionProps {
  selected: string[];
  onChange: (slugs: string[]) => void;
  disabled?: boolean;
}

export const ConnectorPickerSection: React.FC<ConnectorPickerSectionProps> = ({
  selected,
  onChange,
  disabled,
}) => {
  const [connections, setConnections] = useState<UserConnection[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await api.getConnections();
        if (!cancelled) setConnections(data);
      } catch (err) {
        if (!cancelled) {
          setLoadError(getErrorMessage(err, "Failed to load connectors"));
          setConnections([]);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedCount = selected.length;
  const title = selectedCount > 0
    ? `Connected Tools (${selectedCount})`
    : "Connected Tools (optional)";

  // Warn if a selected slug is attached but in a state the agent will skip —
  // EXPIRED, FAILED, INACTIVE all get filtered out by resolve_mcp_servers.
  // Skip INITIATED/INITIALIZING; warning a user who's mid-OAuth that "this
  // won't work" tells them to do the thing they're already doing.
  // Preserve intent — don't unselect.
  const unhealthySelected = useMemo(() => {
    if (!connections) return [] as UserConnection[];
    return connections.filter(
      (c) =>
        (c.status === "EXPIRED" || c.status === "FAILED" || c.status === "INACTIVE") &&
        selected.includes(c.toolkit_slug),
    );
  }, [connections, selected]);

  const toggle = (slug: string) => {
    if (selected.includes(slug)) {
      onChange(selected.filter((s) => s !== slug));
    } else {
      onChange([...selected, slug]);
    }
  };

  return (
    <CollapsibleSection title={title} defaultOpen={selectedCount > 0}>
      <div className="p-4 space-y-3">
        <p className="text-xs text-zinc-500">
          Let the agent also check your connected services.
        </p>

        {loadError && (
          <Alert variant="destructive">
            <AlertDescription>{loadError}</AlertDescription>
          </Alert>
        )}

        {unhealthySelected.length > 0 && (
          <Alert className="border-amber-300 bg-amber-50 text-amber-900">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {unhealthySelected.length === 1
                ? `${unhealthySelected[0].display_name} connection isn't healthy (${unhealthySelected[0].status?.toLowerCase()}). This task will skip it until reconnected.`
                : `${unhealthySelected.length} connections aren't healthy. Tasks will skip them until reconnected.`}
            </AlertDescription>
          </Alert>
        )}

        {selectedCount > ADVISORY_THRESHOLD && (
          <p className="text-xs text-zinc-500 font-mono">
            Attaching many connectors can slow agent runs and increase cost.
          </p>
        )}

        {connections === null ? (
          <p className="text-xs text-zinc-400 font-mono">Loading…</p>
        ) : connections.length === 0 ? (
          <EmptyPickerState />
        ) : (
          <BrutalistTable>
            <BrutalistTableBody>
              {connections.map((conn) => (
                <ConnectorRow
                  key={conn.toolkit_slug}
                  connection={conn}
                  checked={selected.includes(conn.toolkit_slug)}
                  disabled={disabled}
                  onToggle={() => toggle(conn.toolkit_slug)}
                />
              ))}
            </BrutalistTableBody>
          </BrutalistTable>
        )}
      </div>
    </CollapsibleSection>
  );
};

const EmptyPickerState: React.FC = () => (
  <div className="flex items-center gap-3 border-2 border-dashed border-zinc-200 p-4">
    <Plug2 className="h-5 w-5 text-zinc-400 flex-shrink-0" />
    <p className="text-sm text-zinc-600 flex-1">
      No tools connected yet.
    </p>
    <Link
      to="/settings/connectors"
      className="font-mono text-xs uppercase tracking-wider text-zinc-900 hover:underline"
    >
      Connect one →
    </Link>
  </div>
);

interface ConnectorRowProps {
  connection: UserConnection;
  checked: boolean;
  disabled?: boolean;
  onToggle: () => void;
}

const ConnectorRow: React.FC<ConnectorRowProps> = ({
  connection,
  checked,
  disabled,
  onToggle,
}) => {
  const { variant, label } = statusDisplay(connection.status);
  const isExpired = connection.status === "EXPIRED";

  return (
    <BrutalistTableRow
      onClick={disabled ? undefined : onToggle}
      className={cn(isExpired && "bg-amber-50/40")}
    >
      <BrutalistTableCell className="w-10">
        <Checkbox
          checked={checked}
          onCheckedChange={onToggle}
          disabled={disabled}
          aria-label={`Attach ${connection.display_name}`}
          onClick={(e) => e.stopPropagation()}
        />
      </BrutalistTableCell>
      <BrutalistTableCell>
        <div className="flex flex-col">
          <span className="font-medium text-zinc-900">
            {connection.display_name}
          </span>
          <span className="font-mono text-xs text-zinc-500">
            {connection.toolkit_slug}
            {isExpired && " — reconnect required"}
          </span>
        </div>
      </BrutalistTableCell>
      <BrutalistTableCell align="right" className="w-32">
        <StatusBadge variant={variant} label={label} />
      </BrutalistTableCell>
    </BrutalistTableRow>
  );
};

function statusDisplay(
  status: ConnectionStatus | null,
): { variant: StatusVariant; label: string } {
  switch (status) {
    case "ACTIVE":
      return { variant: "active", label: "Active" };
    case "INITIATED":
    case "INITIALIZING":
      return { variant: "pending", label: "Connecting" };
    case "EXPIRED":
      return { variant: "unknown", label: "Expired" };
    case "FAILED":
      return { variant: "failed", label: "Failed" };
    case "INACTIVE":
    case null:
    default:
      return { variant: "paused", label: "Inactive" };
  }
}
