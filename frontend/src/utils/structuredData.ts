import { ChangelogEntry } from "@/types/changelog";

export function generateChangelogStructuredData(entries: ChangelogEntry[]) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Torale Changelog",
    "description": "Product updates and feature releases for Torale AI-powered web monitoring platform",
    "url": "https://torale.ai/changelog",
    "publisher": {
      "@type": "Organization",
      "name": "Torale",
      "url": "https://torale.ai",
      "logo": {
        "@type": "ImageObject",
        "url": "https://torale.ai/logo.svg",
        "width": 512,
        "height": 512
      },
      "sameAs": [
        "https://github.com/prassanna-ravishankar/torale"
      ]
    },
    "mainEntity": {
      "@type": "ItemList",
      "numberOfItems": entries.length,
      "itemListElement": entries.slice(0, 50).map((entry, idx) => ({
        "@type": "ListItem",
        "position": idx + 1,
        "item": {
          "@type": "TechArticle",
          "headline": entry.title,
          "datePublished": entry.date,
          "dateModified": entry.date,
          "articleSection": entry.category,
          "description": entry.description,
          "author": {
            "@type": "Organization",
            "name": "Torale"
          },
          "publisher": {
            "@type": "Organization",
            "name": "Torale"
          }
        }
      }))
    },
    "breadcrumb": {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "https://torale.ai"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "Changelog",
          "item": "https://torale.ai/changelog"
        }
      ]
    }
  };
}
