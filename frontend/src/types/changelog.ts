export interface ChangelogEntry {
  id: string;
  date: string;
  title: string;
  description: string;
  category: "feature" | "improvement" | "fix" | "infra" | "research";
  requestedBy: string[];
  pr?: number | number[];
}
