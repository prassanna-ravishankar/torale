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

  // Scene 1: Hero (0% - 21% of scroll)
  // Actual: 0-100vh in ~485vh total
  const heroProgress = useTransform(scrollYProgress, [0, 0.21], [0, 1]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.18, 0.21], [1, 1, 0]);

  // Scene 2: System (26% - 46% of scroll)
  // Actual: 125-225vh (after 25vh spacer)
  const systemProgress = useTransform(scrollYProgress, [0.26, 0.46], [0, 1]);
  const systemOpacity = useTransform(scrollYProgress, [0.21, 0.30, 0.42, 0.50], [0, 1, 1, 0]);

  // Scene 3: Code (51% - 71% of scroll)
  // Actual: 245-345vh (after 20vh spacer)
  const codeProgress = useTransform(scrollYProgress, [0.51, 0.71], [0, 1]);
  const codeOpacity = useTransform(scrollYProgress, [0.46, 0.55, 0.67, 0.75], [0, 1, 1, 0]);

  // Scene 4: Pricing (76% - 95% of scroll)
  // Actual: 365-465vh (after 20vh spacer)
  const pricingProgress = useTransform(scrollYProgress, [0.76, 0.95], [0, 1]);
  const pricingOpacity = useTransform(scrollYProgress, [0.71, 0.80, 1], [0, 1, 1]);

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
