import { useScroll, useTransform, MotionValue } from "framer-motion";
import { RefObject, useLayoutEffect, useState } from "react";

export interface ScrollProgress {
  // Raw scroll progress (0 to 1)
  scrollYProgress: MotionValue<number>;

  // Scene progress values (0 to 1 within each scene)
  heroProgress: MotionValue<number>;
  systemProgress: MotionValue<number>;
  codeProgress: MotionValue<number>;
  pricingProgress: MotionValue<number>;

  // Scene visibility (0 = hidden, 1 = visible)
  heroOpacity: MotionValue<number>;
  systemOpacity: MotionValue<number>;
  codeOpacity: MotionValue<number>;
  pricingOpacity: MotionValue<number>;
}

type SceneKey = "hero" | "system" | "code" | "pricing";

interface SceneRange {
  start: number;
  end: number;
}

type SceneRanges = Record<SceneKey, SceneRange>;

const DEFAULT_RANGES: SceneRanges = {
  hero: { start: 0, end: 0.24 },
  system: { start: 0.24, end: 0.5 },
  code: { start: 0.5, end: 0.76 },
  pricing: { start: 0.76, end: 1 },
};

const clamp01 = (value: number) => Math.min(1, Math.max(0, value));

const useRangeTransform = (
  scrollYProgress: MotionValue<number>,
  range: SceneRange
) =>
  useTransform(scrollYProgress, [range.start, range.end], [0, 1], {
    clamp: true,
  });

const useOpacityTransform = (
  scrollYProgress: MotionValue<number>,
  range: SceneRange,
  fade: number = 0.08,
  keepTailVisible = false
) => {
  const fadeInStart = clamp01(range.start - fade);
  const fadeOutEnd = keepTailVisible ? 1 : clamp01(range.end + fade);

  const input = keepTailVisible
    ? [fadeInStart, range.start, range.end]
    : [fadeInStart, range.start, range.end, fadeOutEnd];

  const output = keepTailVisible ? [0, 1, 1] : [0, 1, 1, 0];

  return useTransform(scrollYProgress, input, output, { clamp: true });
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
    if (typeof window === "undefined") {
      return;
    }

    const updateRanges = () => {
      const container = containerRef.current;
      if (!container) {
        return;
      }

      const sections = Array.from(
        container.querySelectorAll<HTMLElement>("[data-scene]")
      );

      if (!sections.length) {
        return;
      }

      const scrollableHeight = Math.max(
        container.scrollHeight - window.innerHeight,
        1
      );

      const nextRanges: Partial<SceneRanges> = {};

      sections.forEach((section) => {
        const scene = section.dataset.scene as SceneKey | undefined;
        if (!scene) {
          return;
        }

        const start = clamp01(section.offsetTop / scrollableHeight);
        const end = clamp01(
          (section.offsetTop + section.offsetHeight) / scrollableHeight
        );

        if (end <= start) {
          nextRanges[scene] = {
            start,
            end: clamp01(start + 0.0001),
          };
        } else {
          nextRanges[scene] = { start, end };
        }
      });

      if (Object.keys(nextRanges).length) {
        setSceneRanges((prev) => ({ ...prev, ...nextRanges }));
      }
    };

    updateRanges();
    window.addEventListener("resize", updateRanges);

    return () => {
      window.removeEventListener("resize", updateRanges);
    };
  }, [containerRef]);

  const heroProgress = useRangeTransform(scrollYProgress, sceneRanges.hero);
  const heroOpacity = useOpacityTransform(
    scrollYProgress,
    sceneRanges.hero,
    0.08
  );

  const systemProgress = useRangeTransform(
    scrollYProgress,
    sceneRanges.system
  );
  const systemOpacity = useOpacityTransform(
    scrollYProgress,
    sceneRanges.system
  );

  const codeProgress = useRangeTransform(scrollYProgress, sceneRanges.code);
  const codeOpacity = useOpacityTransform(
    scrollYProgress,
    sceneRanges.code
  );

  const pricingProgress = useRangeTransform(
    scrollYProgress,
    sceneRanges.pricing
  );
  const pricingOpacity = useOpacityTransform(
    scrollYProgress,
    sceneRanges.pricing,
    0.08,
    true
  );

  return {
    scrollYProgress,
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
