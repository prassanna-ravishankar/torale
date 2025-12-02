/**
 * Motion.dev compatibility layer
 *
 * Drop-in replacement for Framer Motion imports.
 * Change: import { motion } from "framer-motion"
 * To:     import { motion } from "@/lib/motion-compat"
 */

export {
  motion,
  AnimatePresence,
  useScroll,
  useTransform,
  useMotionValue,
  useSpring,
} from "motion/react";

// Animation presets for <400ms interactions
export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  },
  slideUp: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 10 },
    transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] },
  },
  hoverLift: {
    whileHover: { y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)", transition: { duration: 0.15 } },
  },
  press: {
    whileTap: { scale: 0.98, y: 1, transition: { duration: 0.1 } },
  },
};
