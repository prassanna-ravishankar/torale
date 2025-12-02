import { motion } from "framer-motion";
import { GitCommit } from "lucide-react";
import { ChangelogEntry } from "@/types/changelog";
import { getCategoryIcon, getCategoryLabel, formatChangelogDate } from "@/utils/changelog";
import { GITHUB_REPO_URL } from "@/constants/links";

interface ChangelogEntryCardProps {
  entry: ChangelogEntry;
  index: number;
}

const TypeBadge = ({ category }: { category: ChangelogEntry["category"] }) => {
  const styles = {
    feature: "bg-emerald-50 text-emerald-700 border-emerald-200",
    improvement: "bg-blue-50 text-blue-700 border-blue-200",
    fix: "bg-amber-50 text-amber-700 border-amber-200",
    infra: "bg-purple-50 text-purple-700 border-purple-200",
    research: "bg-pink-50 text-pink-700 border-pink-200",
  };

  const labels = {
    feature: "NEW FEATURE",
    improvement: "IMPROVEMENT",
    fix: "BUG FIX",
    infra: "INFRASTRUCTURE",
    research: "RESEARCH",
  };

  const IconComponent = getCategoryIcon(category);

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-mono font-bold tracking-wider uppercase ${styles[category]}`}>
      <IconComponent className="w-3 h-3" />
      {labels[category]}
    </div>
  );
};

export function ChangelogEntryCard({ entry, index }: ChangelogEntryCardProps) {
  const formattedDate = formatChangelogDate(entry.date, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const prs = entry.pr ? (Array.isArray(entry.pr) ? entry.pr : [entry.pr]) : [];
  const isEven = index % 2 === 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="relative pl-8 md:pl-0 group"
    >
      {/* Timeline Connector */}
      <div className="absolute left-0 md:left-1/2 top-0 bottom-0 w-px bg-zinc-200 -ml-px md:-ml-0.5" />

      {/* Timeline Node */}
      <div className="absolute left-0 md:left-1/2 top-8 w-3 h-3 bg-white border-2 border-zinc-300 rounded-full -ml-1.5 md:-ml-1.5 z-10 group-hover:border-zinc-900 group-hover:scale-125 transition-all duration-300" />

      {/* Content Card Layout */}
      <div className={`md:flex items-start justify-between md:gap-12 ${isEven ? 'md:flex-row-reverse' : ''}`}>

        {/* Date / Meta (Opposite side on Desktop) */}
        <div className={`hidden md:block w-1/2 pt-8 ${isEven ? 'text-left pl-12' : 'text-right pr-12'}`}>
          <div className="font-mono text-sm text-zinc-400 mb-1">{formattedDate}</div>
          <div className="font-mono text-xs text-zinc-300">#{entry.id}</div>
        </div>

        {/* Card (Main Side) */}
        <div className={`w-full md:w-1/2 mb-12 md:mb-24 ${isEven ? 'md:pr-12' : 'md:pl-12'}`}>
          {/* Mobile Date Header */}
          <div className="md:hidden mb-2 pl-4">
            <span className="font-mono text-xs text-zinc-400">{formattedDate}</span>
          </div>

          <motion.div
            whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.05)" }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="bg-white border border-zinc-200 p-6 md:p-8 rounded-lg shadow-sm transition-colors hover:border-zinc-300 relative group/card"
          >
            {/* Decorative Corner */}
            <div className="absolute top-0 right-0 w-8 h-8 overflow-hidden">
              <div className="absolute top-0 right-0 w-[150%] h-[150%] bg-zinc-50 rotate-45 transform origin-bottom-left border-l border-zinc-100"></div>
            </div>

            {/* ID at top like commit SHA */}
            <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-400 mb-3">
              <GitCommit className="w-3 h-3" />
              <span>#{entry.id}</span>
            </div>

            <div className="flex justify-between items-start mb-4">
              <TypeBadge category={entry.category} />
            </div>

            <h3 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4 leading-tight">
              {entry.title}
            </h3>

            <p className="text-zinc-600 leading-relaxed text-sm md:text-base font-normal">
              {entry.description}
            </p>

            {/* Footer Metadata in Card */}
            <div className="mt-6 pt-4 border-t border-zinc-100 flex items-center justify-between">
              {entry.requestedBy.length > 0 ? (
                <div className="text-[10px] text-zinc-400 italic">
                  Requested by {entry.requestedBy.join(", ")}
                </div>
              ) : (
                <div></div>
              )}
              {prs.length > 0 && (
                <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-400">
                  {prs.map((pr, idx) => (
                    <a
                      key={pr}
                      href={`${GITHUB_REPO_URL}/pull/${pr}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-zinc-900 hover:underline transition-colors"
                      title="View PR on GitHub"
                    >
                      PR #{pr}{idx < prs.length - 1 && ', '}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
