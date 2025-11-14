import { useScroll, useTransform, MotionValue } from "framer-motion";
import { RefObject, useLayoutEffect, useState } from "react";

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
type SceneRanges = Record<SceneKey, { start: number; end: number }>;

const DEFAULT_RANGES: SceneRanges = {
  hero: { start: 0, end: 0.25 },
  system: { start: 0.25, end: 0.5 },
  code: { start: 0.5, end: 0.75 },
  pricing: { start: 0.75, end: 1 },
};

const clamp01 = (value: number) => Math.min(1, Math.max(0, value));

// Helper to map scroll progress to a scene's 0-1 progress
const useRangeTransform = (
  scrollYProgress: MotionValue<number>,
  range: { start: number; end: number }
) => {
  return useTransform(scrollYProgress, [range.start, range.end], [0, 1], {
    clamp: true,
  });
};

export function useScrollProgress(
  containerRef: RefObject<HTMLElement>
): ScrollProgress {
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const [sceneRanges, setSceneRanges] = useState<SceneRanges>(DEFAULT_RANGES);

  useLayoutEffect(() => {
    if (typeof window === "undefined") return;

    const updateRanges = () => {
      const container = containerRef.current;
      if (!container) return;

      const sections = Array.from(
        container.querySelectorAll<HTMLElement>("[data-scene]")
      );
      const footer = container.querySelector<HTMLElement>("footer");

      if (!sections.length || !footer) return;

      const scrollableHeight = Math.max(
        container.scrollHeight - window.innerHeight,
        1
      );

      // Get the 0-1 start point of each scene
      const heroStart = 0;
      const systemStart =
        sections[1].offsetTop / scrollableHeight;
      const codeStart =
        sections[2].offsetTop / scrollableHeight;
      const pricingStart =
        sections[3].offsetTop / scrollableHeight;
      // The "end" is where the footer begins
      const footerStart =
        footer.offsetTop / scrollableHeight;

      // Ensure ranges are contiguous (end = next start)
      const nextRanges: SceneRanges = {
        hero: { start: heroStart, end: systemStart },
        system: { start: systemStart, end: codeStart },
        code: { start: codeStart, end: pricingStart },
        pricing: { start: pricingStart, end: footerStart },
      };

      // Clamp all values
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

  // Scene-specific progress (0-1)
  const heroProgress = useRangeTransform(scrollYProgress, sceneRanges.hero);
  const systemProgress = useRangeTransform(scrollYProgress, sceneRanges.system);
  const codeProgress = useRangeTransform(scrollYProgress, sceneRanges.code);
  const pricingProgress = useRangeTransform(scrollYProgress, sceneRanges.pricing);

  // Cross-fade duration (as a 0-1 percentage)
  const fade = 0.02; // A very small 2% cross-fade

  // Clean Cross-fade Opacity Logic
  const heroOpacity = useTransform(
    scrollYProgress,
    [sceneRanges.hero.end - fade, sceneRanges.hero.end],
    [1, 0],
    { clamp: true }
  );

  const systemOpacity = useTransform(
    scrollYProgress,
    [
      sceneRanges.system.start - fade,
      sceneRanges.system.start + fade,
      sceneRanges.system.end - fade,
      sceneRanges.system.end,
    ],
    [0, 1, 1, 0],
    { clamp: true }
  );

  const codeOpacity = useTransform(
    scrollYProgress,
    [
      sceneRanges.code.start - fade,
      sceneRanges.code.start + fade,
      sceneRanges.code.end - fade,
      sceneRanges.code.end,
    ],
    [0, 1, 1, 0],
    { clamp: true }
  );

  const pricingOpacity = useTransform(
    scrollYProgress,
    // Fade in and stay visible
    [
      sceneRanges.pricing.start - fade,
      sceneRanges.pricing.start + fade,
    ],
    [0, 1],
    { clamp: true }
  );

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
