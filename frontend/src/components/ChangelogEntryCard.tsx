import { motion } from "framer-motion";
import { ChangelogEntry } from "@/types/changelog";
import { getCategoryIcon, getCategoryLabel, formatChangelogDate } from "@/utils/changelog";
import { GITHUB_REPO_URL } from "@/constants/links";

interface ChangelogEntryCardProps {
  entry: ChangelogEntry;
  isEven: boolean;
}

export function ChangelogEntryCard({ entry, isEven }: ChangelogEntryCardProps) {
  const IconComponent = getCategoryIcon(entry.category);
  const formattedDate = formatChangelogDate(entry.date, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  // Normalize PR to always be an array for rendering
  const prs = entry.pr ? (Array.isArray(entry.pr) ? entry.pr : [entry.pr]) : [];

  const content = (
    <motion.div
      className="border-2 border-black bg-white"
      initial={{ borderColor: "#000000" }}
      whileInView={{ borderColor: "#FF0000" }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.2 }}
    >
      <div className="p-6">
        {/* Row 1: Category Badge + Date */}
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <div className="border-2 border-black px-2 py-1 flex items-center gap-2">
            <IconComponent className="h-4 w-4 text-brand-red" />
            <span className="font-mono text-xs uppercase tracking-wider font-bold">
              [ {getCategoryLabel(entry.category)} ]
            </span>
          </div>
          <span className="font-mono text-xs text-brand-grey uppercase tracking-wide">
            {formattedDate}
          </span>
        </div>

        {/* Row 2: Title */}
        <h3 className="text-xl font-bold mb-2 hover:text-brand-red transition-colors">
          {entry.title}
        </h3>

        {/* Row 3: PR Links (always after title) */}
        {prs.length > 0 && (
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            {prs.map((pr, idx) => (
              <a
                key={pr}
                href={`${GITHUB_REPO_URL}/pull/${pr}`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-xs text-black hover:text-brand-red transition-colors font-medium"
                title="View PR on GitHub"
              >
                [ PR #{pr} ]
              </a>
            ))}
          </div>
        )}

        {/* Row 4: Description */}
        <p className="text-sm text-brand-grey leading-relaxed">
          {entry.description}
        </p>

        {/* Row 5: Requested By */}
        {entry.requestedBy.length > 0 && (
          <p className="font-mono text-xs text-brand-grey mt-3">
            [ Requested by: {entry.requestedBy.join(", ")} ]
          </p>
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {isEven ? (
        <>
          <div>{content}</div>
          <div className="hidden md:block" />
        </>
      ) : (
        <>
          <div className="hidden md:block" />
          <div>{content}</div>
        </>
      )}
    </div>
  );
}
