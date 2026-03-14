import React from "react";
import { ActivityStep } from "@/types";
import { CollapsibleSection } from "@/components/torale";
import {
  Search,
  Globe,
  Brain,
  BookOpen,
  Twitter,
  LucideIcon,
} from "lucide-react";

interface AgentActivityProps {
  activity: ActivityStep[];
}

const TOOL_CONFIG: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  perplexity_search: { icon: Search, color: "text-blue-500", label: "Searched" },
  parallel_search: { icon: Search, color: "text-indigo-500", label: "Searched" },
  twitter_search: { icon: Twitter, color: "text-sky-500", label: "Searched X" },
  fetch_url: { icon: Globe, color: "text-emerald-500", label: "Fetched" },
  search_memories: { icon: BookOpen, color: "text-amber-500", label: "Recalled" },
  add_memory: { icon: Brain, color: "text-purple-500", label: "Remembered" },
};

const FALLBACK_CONFIG = { icon: Search, color: "text-zinc-400", label: "Ran" };

// Icon container is 20px (h-5 w-5) centered in 23px wrapper; line offset = 11px = ~center
const ICON_SIZE = "h-[23px] w-[23px]";

export const AgentActivity: React.FC<AgentActivityProps> = ({ activity }) => {
  if (activity.length === 0) return null;

  return (
    <CollapsibleSection
      title={`Agent Activity · ${activity.length} step${activity.length !== 1 ? "s" : ""}`}
      defaultOpen={false}
      className="mb-3"
    >
      <div className="border-x-2 border-b-2 border-zinc-200 bg-zinc-50 p-4">
        <div className="relative">
          <div className="absolute left-[11px] top-3 bottom-3 w-px bg-zinc-200" />

          {activity.map((step, i) => {
            const config = TOOL_CONFIG[step.tool] || FALLBACK_CONFIG;
            const Icon = config.icon;

            return (
              <div
                key={`${step.tool}-${i}`}
                className={`relative flex items-start gap-3 ${i < activity.length - 1 ? "pb-3" : ""}`}
              >
                <div className={`relative z-10 mt-0.5 flex ${ICON_SIZE} shrink-0 items-center justify-center bg-zinc-50`}>
                  <div className={`flex h-5 w-5 items-center justify-center border border-zinc-200 bg-white ${config.color}`}>
                    <Icon className="h-3 w-3" />
                  </div>
                </div>

                <span className="text-xs font-mono text-zinc-600 leading-relaxed pt-0.5 break-words">
                  <span className="text-zinc-400">{config.label}:</span>{" "}
                  {step.detail}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </CollapsibleSection>
  );
};
