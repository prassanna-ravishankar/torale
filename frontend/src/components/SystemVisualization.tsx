import { motion, MotionValue, useTransform } from "framer-motion";
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

export function SystemVisualization({ progress }: SystemVisualizationProps) {
  // Determine active layer for text display
  const activeLayerId = useTransform(progress, (value) => {
    if (value < 0.2) return 0;
    if (value < 0.4) return 1;
    if (value < 0.6) return 2;
    if (value < 0.8) return 3;
    return 4;
  });

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8">
      <div className="max-w-6xl w-full grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
        {/* Left: Diagram */}
        <div className="flex items-center justify-center">
          <SystemDiagram progress={progress} />
        </div>

        {/* Right: Text Content */}
        <div className="flex items-center justify-center">
          <div className="w-full max-w-lg space-y-6 font-mono">
            {layerInfo.map((layer) => {
              const isActive = useTransform(activeLayerId, (id) => id === layer.id);

              return (
                <motion.div
                  key={layer.id}
                  style={{
                    opacity: useTransform(isActive, (active) =>
                      active ? 1 : 0.3
                    ),
                    scale: useTransform(isActive, (active) =>
                      active ? 1 : 0.95
                    ),
                  }}
                  transition={{ duration: 0.2, ease: "linear" }}
                  className="transition-all"
                >
                  <h3 className="text-2xl font-bold mb-3 tracking-wider">
                    {layer.title}
                  </h3>
                  <motion.p
                    style={{
                      opacity: useTransform(isActive, (active) =>
                        active ? 1 : 0
                      ),
                      height: useTransform(isActive, (active) =>
                        active ? "auto" : "0px"
                      ),
                    }}
                    className="text-brand-grey leading-relaxed overflow-hidden"
                  >
                    {layer.description}
                  </motion.p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
