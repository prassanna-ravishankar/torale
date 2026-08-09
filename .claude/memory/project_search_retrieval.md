# Search retrieval is independent from the reasoning model

- webwhen deliberately does not use Gemini native Google Search grounding in production.
- The November 2025 grounded-search evaluation selected Perplexity: 80% accuracy versus 60% for Gemini Grounded on the recorded cases (PR #34, commit `687fdc2`).
- The January 2026 agent migration made this an architectural boundary: Gemini reasons while explicit Perplexity tools retrieve evidence (PR #136, commit `aa221a0`).
- Parallel was added in March 2026 because it surfaced different authoritative primary sources; its recorded eval passed 9/9 cases without notification-accuracy regression (PR #174, commit `3adb07e`).
- Keep search providers as explicit, provider-shaped tools so model evals compare reasoning against the same retrieval layer. Do not adopt Pydantic AI/provider-native web search merely for convenience; require a webwhen-specific eval showing a material improvement.
- Gemini grounding previously also required cleanup of Vertex redirect citation URLs, but that was secondary to the measured quality and architecture decisions.
