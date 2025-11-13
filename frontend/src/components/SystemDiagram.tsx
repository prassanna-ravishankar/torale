import { motion, MotionValue, useTransform } from "framer-motion";
import { Grid3x3, Database, Cpu, Bell } from "lucide-react";

interface LayerData {
  id: number;
  title: string;
  Icon: React.ElementType;
  visual: "grid" | "bars" | "circuit" | "signal";
}

const layers: LayerData[] = [
  { id: 1, title: "FOUNDATION", Icon: Grid3x3, visual: "grid" },
  { id: 2, title: "ACQUISITION", Icon: Database, visual: "bars" },
  { id: 3, title: "REASONING", Icon: Cpu, visual: "circuit" },
  { id: 4, title: "SIGNAL", Icon: Bell, visual: "signal" },
];

interface SystemDiagramProps {
  progress: MotionValue<number>;
}

// Visual representations for each layer
const LayerVisual = ({ visual }: { visual: LayerData["visual"] }) => {
  switch (visual) {
    case "grid":
      return (
        <div className="grid grid-cols-4 gap-1 p-2">
          {Array.from({ length: 16 }).map((_, i) => (
            <div key={i} className="w-full aspect-square bg-black/10" />
          ))}
        </div>
      );

    case "bars":
      return (
        <div className="flex items-end justify-around gap-1 p-2 h-16">
          {[60, 80, 40, 90, 70].map((height, i) => (
            <div
              key={i}
              className="flex-1 bg-black/20"
              style={{ height: `${height}%` }}
            />
          ))}
        </div>
      );

    case "circuit":
      return (
        <div className="relative p-4">
          <div className="absolute inset-4 border-2 border-black/10" />
          <div className="absolute inset-6 border border-black/10" />
          <div className="w-12 h-12 border-2 border-black/20 mx-auto" />
        </div>
      );

    case "signal":
      return (
        <div className="relative p-4 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-black/10 absolute" />
          <div className="w-16 h-16 border border-black/5 absolute" />
          <div className="w-4 h-4 bg-black/30" />
        </div>
      );
  }
};

export function SystemDiagram({ progress }: SystemDiagramProps) {
  // Calculate which layer should be active based on scroll progress
  // progress: 0 = all inactive, 0.25 = layer 1, 0.5 = layer 2, 0.75 = layer 3, 1 = layer 4
  const activeLayer = useTransform(progress, (value) => {
    if (value < 0.2) return 0; // None active initially
    if (value < 0.4) return 1;
    if (value < 0.6) return 2;
    if (value < 0.8) return 3;
    return 4;
  });

  return (
    <div className="w-full max-w-md mx-auto space-y-4 font-mono">
      {layers.map((layer, index) => {
        // Each layer's opacity and scale based on whether it's active
        const layerOpacity = useTransform(activeLayer, (active) =>
          active === layer.id ? 1 : 0.4
        );
        const layerScale = useTransform(activeLayer, (active) =>
          active === layer.id ? 1.05 : 1
        );
        const borderColor = useTransform(activeLayer, (active) =>
          active === layer.id ? "#FF0000" : "#000000"
        );

        return (
          <motion.div
            key={layer.id}
            style={{
              opacity: layerOpacity,
              scale: layerScale,
            }}
            className="relative"
            transition={{ duration: 0.2, ease: "linear" }}
          >
            <motion.div
              style={{ borderColor }}
              className="border-2 bg-white p-4 flex items-center gap-4 transition-colors duration-200"
            >
              {/* Layer number and icon */}
              <div className="flex flex-col items-center gap-2 min-w-[80px]">
                <span className="text-xl font-bold">[ {layer.id} ]</span>
                <layer.Icon className="w-6 h-6" />
              </div>

              {/* Visual representation */}
              <div className="flex-1 border border-black/20">
                <LayerVisual visual={layer.visual} />
              </div>

              {/* Layer title */}
              <div className="min-w-[120px] text-right">
                <span className="text-sm font-bold tracking-wider">
                  {layer.title}
                </span>
              </div>
            </motion.div>
          </motion.div>
        );
      })}
    </div>
  );
}
