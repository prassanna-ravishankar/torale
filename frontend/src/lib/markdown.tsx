import type { Components } from 'react-markdown';

/** Compact markdown styling for previews and summaries (tight spacing). */
export const markdownCompact: Components = {
  p: ({ children }) => <p className="mb-0 leading-relaxed text-zinc-700">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-5 mb-0 space-y-0">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 mb-0 space-y-0">{children}</ol>,
  li: ({ children }) => <li className="text-sm leading-relaxed text-zinc-700">{children}</li>,
  strong: ({ children }) => <strong className="font-bold text-zinc-900">{children}</strong>,
};

/** Full markdown styling for detailed content (standard spacing + headings). */
export const markdownFull: Components = {
  p: ({ children }) => <p className="mb-3 leading-relaxed text-zinc-900">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5">{children}</ol>,
  li: ({ children }) => <li className="text-sm leading-relaxed text-zinc-700">{children}</li>,
  strong: ({ children }) => <strong className="font-bold text-zinc-900">{children}</strong>,
  h1: ({ children }) => <h1 className="text-xl font-grotesk font-bold mb-3 mt-4 text-zinc-900">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-grotesk font-bold mb-2 mt-3 text-zinc-900">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-grotesk font-bold mb-2 mt-2 text-zinc-900">{children}</h3>,
};
