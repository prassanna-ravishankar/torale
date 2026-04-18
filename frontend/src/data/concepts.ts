/**
 * Concept data for public SEO landing pages explaining how Torale works.
 * Used by ConceptPage.tsx (route: /concepts/:concept).
 *
 * Shape mirrors competitors.ts and useCases.ts so the same meta/sitemap
 * plumbing applies uniformly.
 */

export interface ConceptSection {
  heading: string;
  body: string;
}

export interface ConceptData {
  name: string;
  tagline: string;
  metaTitle: string;
  metaDescription: string;
  heroTitle: string;
  heroSubtitle: string;
  /**
   * Ordered long-form sections rendered as h2+paragraphs. Markdown-ish; keep
   * paragraphs in a single string — no escape interpretation here.
   */
  sections: ConceptSection[];
  faq: {
    question: string;
    answer: string;
  }[];
  /** Optional links out to related concept/use-case/compare pages. */
  relatedLinks?: {
    href: string;
    label: string;
  }[];
  /** Optional link to a deeper engineering doc on docs.torale.ai. */
  engineeringDoc?: {
    href: string;
    label: string;
  };
}

export const CONCEPTS: Record<string, ConceptData> = {};
