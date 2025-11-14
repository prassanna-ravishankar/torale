import { useScroll, MotionValue } from "framer-motion";
import { RefObject, useLayoutEffect, useState } from "react";
import {
  SceneRange,
  CROSS_FADE_DURATION,
  clamp01,
  useRangeTransform,
  createCrossFadeOpacity,
  createFirstSceneOpacity,
  createLastSceneOpacity,
} from "@/utils/scrollProgress";

// ============================================================================
// TYPES
// ============================================================================

export interface ScrollProgress {
  heroProgress: MotionValue<number>;
  systemProgress: MotionValue<number>;
  codeProgress: MotionValue<number>;
  pricingProgress: MotionValue<number>;
  heroOpacity: MotionValue<number>;
  systemOpacity: MotionValue<number>;
  codeOpacity: MotionValue<number>;
  pricingOpacity: MotionValue<number>;
}

type SceneKey = "hero" | "system" | "code" | "pricing";
type SceneRanges = Record<SceneKey, SceneRange>;

// ============================================================================
// CONSTANTS
// ============================================================================

// Default fallback ranges (used until layout is measured)
const DEFAULT_RANGES: SceneRanges = {
  hero: { start: 0, end: 0.25 },
  system: { start: 0.25, end: 0.5 },
  code: { start: 0.5, end: 0.75 },
  pricing: { start: 0.75, end: 1 },
};

// ============================================================================
// MAIN HOOK
// ============================================================================

export function useScrollProgress(
  containerRef: RefObject<HTMLElement>
): ScrollProgress {
  // ---------------------------------------------------------------------------
  // 1. Setup framer-motion scroll tracking
  // ---------------------------------------------------------------------------

  // Track container movement through viewport
  // scrollYProgress goes from 0 (container top hits viewport top)
  // to 1 (container bottom hits viewport bottom)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const [sceneRanges, setSceneRanges] = useState<SceneRanges>(DEFAULT_RANGES);

  // ---------------------------------------------------------------------------
  // 2. Calculate dynamic scroll ranges based on actual DOM layout
  // ---------------------------------------------------------------------------

  useLayoutEffect(() => {
    if (typeof window === "undefined") return;

    const updateRanges = () => {
      const container = containerRef.current;
      if (!container) return;

      // Find all scene sections and the footer
      const sections = Array.from(
        container.querySelectorAll<HTMLElement>("[data-scene]")
      );
      const footer = container.querySelector<HTMLElement>("footer");

      if (!sections.length || !footer) return;

      // Calculate total container height
      // scrollYProgress goes 0→1 as container moves through viewport
      // So we normalize section positions against container's total height
      const containerHeight = container.scrollHeight;

      // Get normalized (0-1) positions within the container
      // These positions match the scrollYProgress coordinate system
      const heroStart = 0;
      const systemStart = sections[1].offsetTop / containerHeight;
      const codeStart = sections[2].offsetTop / containerHeight;
      const pricingStart = sections[3].offsetTop / containerHeight;
      const footerStart = footer.offsetTop / containerHeight;

      // Make ranges contiguous: each scene's end = next scene's start
      // This eliminates "dead zones" between scenes
      const nextRanges: SceneRanges = {
        hero: { start: heroStart, end: systemStart },
        system: { start: systemStart, end: codeStart },
        code: { start: codeStart, end: pricingStart },
        pricing: { start: pricingStart, end: footerStart },
      };

      // Clamp all values to 0-1 range
      Object.keys(nextRanges).forEach((key) => {
        const k = key as SceneKey;
        nextRanges[k].start = clamp01(nextRanges[k].start);
        nextRanges[k].end = clamp01(nextRanges[k].end);
      });

      setSceneRanges(nextRanges);
    };

    updateRanges();
    window.addEventListener("resize", updateRanges);
    return () => window.removeEventListener("resize", updateRanges);
  }, [containerRef]);

  // ---------------------------------------------------------------------------
  // 3. Create progress motion values (0-1 within each scene)
  // ---------------------------------------------------------------------------

  const heroProgress = useRangeTransform(scrollYProgress, sceneRanges.hero);
  const systemProgress = useRangeTransform(scrollYProgress, sceneRanges.system);
  const codeProgress = useRangeTransform(scrollYProgress, sceneRanges.code);
  const pricingProgress = useRangeTransform(scrollYProgress, sceneRanges.pricing);

  // ---------------------------------------------------------------------------
  // 4. Create opacity motion values for cross-fade effect
  // ---------------------------------------------------------------------------

  const fade = CROSS_FADE_DURATION;

  // Hero: Fades out as system starts (no fade-in since it's first)
  const heroOpacity = createFirstSceneOpacity(
    scrollYProgress,
    sceneRanges.system.start,
    fade
  );

  // System: Fades in and out
  const systemOpacity = createCrossFadeOpacity(
    scrollYProgress,
    sceneRanges.system,
    fade
  );

  // Code: Fades in and out
  const codeOpacity = createCrossFadeOpacity(
    scrollYProgress,
    sceneRanges.code,
    fade
  );

  // Pricing: Fades in and stays visible (no fade-out since it's last)
  const pricingOpacity = createLastSceneOpacity(
    scrollYProgress,
    sceneRanges.pricing,
    fade
  );

  // ---------------------------------------------------------------------------
  // 5. Return all motion values
  // ---------------------------------------------------------------------------

  return {
    heroProgress,
    systemProgress,
    codeProgress,
    pricingProgress,
    heroOpacity,
    systemOpacity,
    codeOpacity,
    pricingOpacity,
  };
}
