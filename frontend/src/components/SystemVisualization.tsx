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

// Corner bracket component
const CornerBracket = ({ className }: { className: string }) => (
  <div className={`absolute w-3 h-3 border-brand-red ${className}`} />
);

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
            {/* Render all titles */}
            <div className="space-y-4">
              {layerInfo.map((layer) => {
                const isActive = useTransform(
                  activeLayerId,
                  (id) => id === layer.id
                );
                const textOpacity = useTransform(isActive, (active) =>
                  active ? 1 : 0.4
                );
                const textScale = useTransform(isActive, (active) =>
                  active ? 1 : 0.95
                );
                const bracketOpacity = useTransform(isActive, (active) =>
                  active ? 1 : 0
                );

                return (
                  <div key={layer.id} className="relative">
                    {/* Corner Brackets - only visible when active */}
                    <motion.div style={{ opacity: bracketOpacity }}>
                      <CornerBracket className="top-0 left-0 border-t-2 border-l-2 transition-opacity duration-300" />
                      <CornerBracket className="top-0 right-0 border-t-2 border-r-2 transition-opacity duration-300" />
                      <CornerBracket className="bottom-0 left-0 border-b-2 border-l-2 transition-opacity duration-300" />
                      <CornerBracket className="bottom-0 right-0 border-b-2 border-r-2 transition-opacity duration-300" />
                    </motion.div>

                    {/* Title */}
                    <motion.h3
                      style={{
                        opacity: textOpacity,
                        scale: textScale,
                      }}
                      className="text-xl md:text-2xl font-bold mb-2 tracking-wider py-2 px-4 transition-all duration-300"
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
            <div className="min-h-[80px]">
              {layerInfo.map((layer) => {
                const isActive = useTransform(
                  activeLayerId,
                  (id) => id === layer.id
                );
                const descOpacity = useTransform(isActive, (active) =>
                  active ? 1 : 0
                );
                const descHeight = useTransform(isActive, (active) =>
                  active ? "auto" : "0px"
                );

                return (
                  <motion.p
                    key={layer.id}
                    style={{
                      opacity: descOpacity,
                      height: descHeight,
                    }}
                    className="text-brand-grey leading-relaxed overflow-hidden"
                  >
                    {layer.description}
                  </motion.p>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
