import { useState } from "react";
import { AnimatePresence, motion, MotionValue, useMotionValueEvent } from "framer-motion";
import { SystemDiagram } from "./SystemDiagram";

interface LayerInfo {
  id: number;
  title: string;
  description: string;
}

const layerInfo: LayerInfo[] = [
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

interface SystemVisualizationProps {
  progress: MotionValue<number>;
}

// Corner bracket component
const CornerBracket = ({ className }: { className: string }) => (
  <div className={`absolute w-3 h-3 border-brand-red ${className}`} />
);

const getLayerFromProgress = (value: number): number => {
  if (value < 0.2) return 0;
  if (value < 0.4) return 1;
  if (value < 0.6) return 2;
  if (value < 0.8) return 3;
  return 4;
};

export function SystemVisualization({ progress }: SystemVisualizationProps) {
  const [activeLayer, setActiveLayer] = useState<LayerInfo["id"]>(0);

  useMotionValueEvent(progress, "change", (value) => {
    const normalized = Math.max(0, Math.min(1, value ?? 0));
    const next = getLayerFromProgress(normalized);
    setActiveLayer((prev) => (prev === next ? prev : next));
  });

  const activeLayerInfo =
    layerInfo.find((layer) => layer.id === activeLayer) ?? layerInfo[0];

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
            {/* Render all titles */}
            <div className="space-y-4">
              {layerInfo.map((layer) => {
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

            {/* Divider */}
            <hr className="border-brand-grid w-1/4" />

            {/* Active description with fade-in animation */}
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
          </div>
        </div>
      </div>
    </div>
  );
}
