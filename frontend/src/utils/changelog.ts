import { Zap, TrendingUp, Bug, Server, FlaskConical } from "lucide-react";

export const getCategoryIcon = (category: string) => {
  switch (category) {
    case "feature":
      return Zap;
    case "improvement":
      return TrendingUp;
    case "fix":
      return Bug;
    case "infra":
      return Server;
    case "research":
      return FlaskConical;
    default:
      return Zap;
  }
};

export const getCategoryLabel = (category: string) => {
  switch (category) {
    case "feature":
      return "New Feature";
    case "improvement":
      return "Improvement";
    case "fix":
      return "Bug Fix";
    case "infra":
      return "Infrastructure";
    case "research":
      return "Research";
    default:
      return "Update";
  }
};

/**
 * Format a date string to avoid timezone issues
 * Appends T00:00:00 to ensure date is parsed in local timezone
 */
export const formatChangelogDate = (dateStr: string, options: Intl.DateTimeFormatOptions) => {
  return new Date(`${dateStr}T00:00:00`).toLocaleDateString("en-US", options);
};
