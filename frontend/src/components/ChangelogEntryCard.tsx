import { motion } from "framer-motion";
import { Card, CardHeader } from "@/components/ui/card";
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

  const content = (
    <motion.div
      className="rounded-lg border-2 overflow-hidden"
      initial={{ borderColor: "hsl(var(--border))" }}
      whileInView={{ borderColor: "hsl(var(--primary))", scale: 1.02 }}
      viewport={{ once: true, margin: "-200px" }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-0">
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: "-200px" }}
          transition={{ duration: 0.3 }}
        />
        <CardHeader className="p-6 relative">
          <div className={`flex flex-col ${isEven ? "items-end" : "items-start"}`}>
            <div className="flex items-center gap-2 mb-1">
              {isEven && entry.pr && (
                <a
                  href={`${GITHUB_REPO_URL}/pull/${entry.pr}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] font-mono text-muted-foreground/70 hover:text-primary hover:underline transition-colors"
                  title="View PR on GitHub"
                >
                  #{entry.pr}
                </a>
              )}
              <span className={`text-[9px] font-semibold uppercase tracking-wide text-primary ${isEven ? "order-2" : ""}`}>
                {getCategoryLabel(entry.category)}
              </span>
              <span className="text-xs text-muted-foreground">
                {formattedDate}
              </span>
              {!isEven && entry.pr && (
                <a
                  href={`${GITHUB_REPO_URL}/pull/${entry.pr}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] font-mono text-muted-foreground/70 hover:text-primary hover:underline transition-colors"
                  title="View PR on GitHub"
                >
                  #{entry.pr}
                </a>
              )}
            </div>
            <div className={`flex items-center gap-3 mb-2 ${isEven ? "flex-row-reverse" : ""}`}>
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
                <IconComponent className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-lg font-bold group-hover:text-primary transition-colors">
                {entry.title}
              </h3>
            </div>
            <p className={`text-sm text-muted-foreground leading-relaxed ${isEven ? "text-right" : ""}`}>
              {entry.description}
            </p>
            {entry.requestedBy.length > 0 && (
              <p className="text-xs text-muted-foreground/70 mt-3">
                Requested by {entry.requestedBy.join(", ")}
              </p>
            )}
          </div>
        </CardHeader>
      </Card>
    </motion.div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {isEven ? (
        <>
          <div className="text-right">{content}</div>
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
