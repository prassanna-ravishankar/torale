// ============================================================================
// LANDING PAGE CONSTANTS
// ============================================================================

/**
 * Information for each system layer in the visualization
 */
export interface LayerInfo {
  id: number;
  title: string;
  description: string;
}

export const LAYER_INFO: LayerInfo[] = [
  {
    id: 0,
    title: "[ MONITORING IS A SYSTEM ]",
    description:
      "Torale runs scheduled searches, LLM analysis, and notifications as a unified, automated system.",
  },
  {
    id: 1,
    title: "[ 1. FOUNDATION ]",
    description:
      "Your search query, condition, and cron schedule form the solid foundation for the entire monitoring task.",
  },
  {
    id: 2,
    title: "[ 2. ACQUISITION ]",
    description:
      "At your scheduled time, Torale executes a grounded Google Search, pulling in real-time data from the live web.",
  },
  {
    id: 3,
    title: "[ 3. REASONING ]",
    description:
      "The LLM 'brain' reasons over the search results, evaluating the raw data against your specific condition.",
  },
  {
    id: 4,
    title: "[ 4. SIGNAL ]",
    description:
      "You get the signal. A single, actionable alert is sent only when your condition is met. No noise.",
  },
];

/**
 * 3D layer configuration for the system diagram
 */
export interface LayerConfig {
  id: number;
  title: string;
  yOffset: number;
}

export const LAYER_CONFIGS: LayerConfig[] = [
  { id: 1, title: "FOUNDATION", yOffset: -60 },
  { id: 2, title: "ACQUISITION", yOffset: -20 },
  { id: 3, title: "REASONING", yOffset: 20 },
  { id: 4, title: "SIGNAL", yOffset: 60 },
];

/**
 * Maps scroll progress (0-1) to active layer ID
 */
export function getLayerFromProgress(value: number): number {
  if (value < 0.2) return 0;
  if (value < 0.4) return 1;
  if (value < 0.6) return 2;
  if (value < 0.8) return 3;
  return 4;
}
