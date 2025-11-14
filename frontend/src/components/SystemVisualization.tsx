import { useState } from "react";
import { AnimatePresence, motion, MotionValue, useMotionValueEvent } from "framer-motion";
import { SystemDiagram } from "./SystemDiagram";
import { LAYER_INFO, getLayerFromProgress, type LayerInfo } from "@/constants/landing";

// ============================================================================
// TYPES
// ============================================================================

interface SystemVisualizationProps {
  progress: MotionValue<number>;
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Corner bracket decoration that appears on active layer title
 */
const CornerBracket = ({ className }: { className: string }) => (
  <div className={`absolute w-3 h-3 border-brand-red ${className}`} />
);

/**
 * Renders all layer titles with highlighting on active layer
 */
const LayerTitles = ({ activeLayer }: { activeLayer: LayerInfo["id"] }) => (
  <div className="space-y-4">
    {LAYER_INFO.map((layer) => {
      const isActive = activeLayer === layer.id;

      return (
        <div key={layer.id} className="relative">
          {/* Corner Brackets - only visible when active */}
          <motion.div
            animate={{ opacity: isActive ? 1 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <CornerBracket className="top-0 left-0 border-t-2 border-l-2" />
            <CornerBracket className="top-0 right-0 border-t-2 border-r-2" />
            <CornerBracket className="bottom-0 left-0 border-b-2 border-l-2" />
            <CornerBracket className="bottom-0 right-0 border-b-2 border-r-2" />
          </motion.div>

          {/* Title */}
          <motion.h3
            animate={{
              opacity: isActive ? 1 : 0.4,
              scale: isActive ? 1 : 0.95,
              color: isActive ? "#FF0000" : "#000000",
            }}
            transition={{ duration: 0.3 }}
            className="text-xl md:text-2xl font-bold mb-2 tracking-wider py-2 px-4"
          >
            {layer.title}
          </motion.h3>
        </div>
      );
    })}
  </div>
);

/**
 * Renders the description text for the active layer
 */
const LayerDescription = ({ activeLayerInfo }: { activeLayerInfo: LayerInfo }) => (
  <div className="min-h-[80px] relative">
    <AnimatePresence mode="wait">
      <motion.p
        key={activeLayerInfo.id}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3 }}
        className="text-brand-grey leading-relaxed"
      >
        {activeLayerInfo.description}
      </motion.p>
    </AnimatePresence>
  </div>
);

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function SystemVisualization({ progress }: SystemVisualizationProps) {
  const [activeLayer, setActiveLayer] = useState<LayerInfo["id"]>(0);

  // Track scroll progress and update active layer
  useMotionValueEvent(progress, "change", (value) => {
    const normalized = Math.max(0, Math.min(1, value ?? 0));
    const next = getLayerFromProgress(normalized);
    setActiveLayer((prev) => (prev === next ? prev : next));
  });

  const activeLayerInfo =
    LAYER_INFO.find((layer) => layer.id === activeLayer) ?? LAYER_INFO[0];

  return (
    <div className="h-full flex items-center justify-center p-4 md:p-8">
      <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
        {/* Left: Diagram */}
        <div className="flex items-center justify-center">
          <SystemDiagram activeLayer={activeLayer} />
        </div>

        {/* Right: Text Content */}
        <div className="flex items-center justify-center">
          <div className="w-full max-w-lg space-y-6 font-mono">
            <LayerTitles activeLayer={activeLayer} />
            <hr className="border-brand-grid w-1/4" />
            <LayerDescription activeLayerInfo={activeLayerInfo} />
          </div>
        </div>
      </div>
    </div>
  );
}
