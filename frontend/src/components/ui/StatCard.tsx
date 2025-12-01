import { ArrowUpRight } from "lucide-react";

/**
 * StatCard - KPI display card for dashboard stats
 * From MockDashboard.tsx lines 115-128
 */

interface StatCardProps {
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
}

export const StatCard = ({ label, value, trend, trendUp }: StatCardProps) => (
  <div className="bg-white p-4 border border-zinc-200 shadow-sm">
    <div className="text-[10px] font-mono uppercase text-zinc-400 mb-2">{label}</div>
    <div className="flex items-end justify-between">
      <div className="text-2xl font-bold font-grotesk text-zinc-900">{value}</div>
      {trend && (
        <div className={`text-xs font-mono flex items-center gap-1 ${trendUp ? 'text-emerald-600' : 'text-red-600'}`}>
          {trend}
          <ArrowUpRight className={`w-3 h-3 ${!trendUp && 'rotate-90'}`} />
        </div>
      )}
    </div>
  </div>
);
