import { useTransform, MotionValue } from "framer-motion";

// ============================================================================
// TYPES
// ============================================================================

export interface SceneRange {
  start: number;
  end: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

// Cross-fade duration (as a 0-1 percentage of total scroll)
export const CROSS_FADE_DURATION = 0.02; // 2% of total scroll

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Clamps a value between 0 and 1
 */
export const clamp01 = (value: number): number => Math.min(1, Math.max(0, value));

/**
 * Maps scroll progress to a scene's internal 0-1 progress
 */
export const useRangeTransform = (
  scrollYProgress: MotionValue<number>,
  range: SceneRange
): MotionValue<number> => {
  return useTransform(scrollYProgress, [range.start, range.end], [0, 1], {
    clamp: true,
  });
};

/**
 * Creates opacity transform for a scene that fades in and out
 */
export const createCrossFadeOpacity = (
  scrollYProgress: MotionValue<number>,
  range: SceneRange,
  fade: number
): MotionValue<number> => {
  return useTransform(
    scrollYProgress,
    [
      range.start - fade,
      range.start + fade,
      range.end - fade,
      range.end,
    ],
    [0, 1, 1, 0],
    { clamp: true }
  );
};

/**
 * Creates opacity transform for first scene (no fade-in)
 */
export const createFirstSceneOpacity = (
  scrollYProgress: MotionValue<number>,
  nextSceneStart: number,
  fade: number
): MotionValue<number> => {
  return useTransform(
    scrollYProgress,
    [nextSceneStart - fade, nextSceneStart],
    [1, 0],
    { clamp: true }
  );
};

/**
 * Creates opacity transform for last scene (no fade-out)
 */
export const createLastSceneOpacity = (
  scrollYProgress: MotionValue<number>,
  range: SceneRange,
  fade: number
): MotionValue<number> => {
  return useTransform(
    scrollYProgress,
    [range.start - fade, range.start + fade],
    [0, 1],
    { clamp: true }
  );
};
