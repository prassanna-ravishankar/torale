import { useScroll, useTransform, MotionValue } from "framer-motion";
import { RefObject } from "react";

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

export function useScrollProgress(containerRef: RefObject<HTMLElement>): ScrollProgress {
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Scene 1: Hero (0% - 20% of scroll)
  const heroProgress = useTransform(scrollYProgress, [0, 0.2], [0, 1]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15, 0.2], [1, 1, 0]);

  // Scene 2: System (20% - 50% of scroll)
  const systemProgress = useTransform(scrollYProgress, [0.2, 0.5], [0, 1]);
  const systemOpacity = useTransform(scrollYProgress, [0.15, 0.25, 0.45, 0.5], [0, 1, 1, 0]);

  // Scene 3: Code (50% - 70% of scroll)
  const codeProgress = useTransform(scrollYProgress, [0.5, 0.7], [0, 1]);
  const codeOpacity = useTransform(scrollYProgress, [0.45, 0.55, 0.65, 0.7], [0, 1, 1, 0]);

  // Scene 4: Pricing (70% - 90% of scroll)
  const pricingProgress = useTransform(scrollYProgress, [0.7, 0.9], [0, 1]);
  const pricingOpacity = useTransform(scrollYProgress, [0.65, 0.75, 1], [0, 1, 1]);

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
