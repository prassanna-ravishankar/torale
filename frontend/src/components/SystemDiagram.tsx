import { motion, MotionValue, useTransform } from "framer-motion";

interface LayerData {
  id: number;
  title: string;
}

const layers: LayerData[] = [
  { id: 1, title: "FOUNDATION" },
  { id: 2, title: "ACQUISITION" },
  { id: 3, title: "REASONING" },
  { id: 4, title: "SIGNAL" },
];

interface SystemDiagramProps {
  progress: MotionValue<number>;
}

// 1. Foundation: Live Data Grid with flicker animation
const FoundationVisual = () => (
  <div className="w-full h-full p-3 grid grid-cols-6 gap-1.5">
    {Array.from({ length: 36 }).map((_, i) => (
      <div
        key={i}
        className="w-full h-full bg-black/10"
        style={{
          animation: `flicker 4s infinite`,
          animationDelay: `${Math.random() * 4}s`,
        }}
      />
    ))}
  </div>
);

// 2. Acquisition: Rising Data Pillars
const AcquisitionVisual = () => (
  <div className="w-full h-full p-4 grid grid-cols-3 gap-4">
    {Array.from({ length: 9 }).map((_, i) => (
      <div
        key={i}
        className="w-full h-full bg-black/20"
        style={{
          transformOrigin: "bottom",
          animation: `rise ${2 + Math.random() * 2}s infinite alternate ease-in-out`,
          animationDelay: `${i * 0.2}s`,
        }}
      />
    ))}
  </div>
);

// 3. Reasoning: Active CPU with tracers
const ReasoningVisual = () => (
  <div className="w-full h-full flex items-center justify-center p-4 relative">
    {/* Horizontal tracers */}
    <div
      className="absolute top-1/3 left-0 w-1/4 h-0.5 bg-brand-red"
      style={{ animation: "trace-x 2s linear infinite", animationDelay: "0s" }}
    />
    <div
      className="absolute top-1/2 left-0 w-1/4 h-0.5 bg-brand-red"
      style={{ animation: "trace-x 2s linear infinite", animationDelay: "0.5s" }}
    />
    <div
      className="absolute top-2/3 left-0 w-1/4 h-0.5 bg-brand-red"
      style={{ animation: "trace-x 2s linear infinite", animationDelay: "0.2s" }}
    />
    {/* Vertical tracers */}
    <div
      className="absolute left-1/3 top-0 w-0.5 h-1/4 bg-brand-red"
      style={{ animation: "trace-y 1.8s linear infinite", animationDelay: "0.7s" }}
    />
    <div
      className="absolute left-2/3 top-0 w-0.5 h-1/4 bg-brand-red"
      style={{ animation: "trace-y 1.8s linear infinite", animationDelay: "0.3s" }}
    />

    {/* Chip Body */}
    <div className="w-3/4 h-3/4 bg-black/70 relative flex items-center justify-center">
      {/* Etchings */}
      <div className="absolute w-[90%] h-[90%] border border-black/60" />
      <div className="absolute w-[80%] h-[80%] border border-black/60" />

      {/* Core */}
      <div
        className="w-1/2 h-1/2 bg-black/50 relative z-10"
        style={{ animation: "pulse-core 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}
      />
    </div>
  </div>
);

// 4. Signal: Beacon with expanding rings
const SignalVisual = () => (
  <div className="w-full h-full flex items-center justify-center relative">
    {/* Signal Rings */}
    <div
      className="absolute w-16 h-16 border-2 border-brand-red/70"
      style={{ animation: "signal-ring 2.5s ease-out infinite", animationDelay: "0s" }}
    />
    <div
      className="absolute w-16 h-16 border-2 border-brand-red/70"
      style={{ animation: "signal-ring 2.5s ease-out infinite", animationDelay: "1.25s" }}
    />

    {/* Central Beacon */}
    <div
      className="w-8 h-8 bg-brand-red opacity-90 z-10"
      style={{
        animation: "pulse-core 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        boxShadow: "0 0 20px 10px rgba(255, 0, 0, 0.4)",
      }}
    />
  </div>
);

// Map layer ID to visual component
const LayerVisual = ({ layerId }: { layerId: number }) => {
  switch (layerId) {
    case 1:
      return <FoundationVisual />;
    case 2:
      return <AcquisitionVisual />;
    case 3:
      return <ReasoningVisual />;
    case 4:
      return <SignalVisual />;
    default:
      return null;
  }
};

export function SystemDiagram({ progress }: SystemDiagramProps) {
  // Calculate which layer should be active based on scroll progress
  const activeLayer = useTransform(progress, (value) => {
    if (value < 0.2) return 0; // None active initially
    if (value < 0.4) return 1;
    if (value < 0.6) return 2;
    if (value < 0.8) return 3;
    return 4;
  });

  return (
    <div className="w-full max-w-4xl mx-auto font-mono">
      {/* Horizontal row of layers */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {layers.map((layer) => {
          // Each layer's opacity, scale, and border based on whether it's active
          const layerOpacity = useTransform(activeLayer, (active) =>
            active === layer.id ? 1 : 0.3
          );
          const layerScale = useTransform(activeLayer, (active) =>
            active === layer.id ? 1.05 : 0.95
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
              className="flex flex-col"
              transition={{ duration: 0.7, ease: "easeInOut" }}
            >
              <motion.div
                style={{ borderColor }}
                className="w-full aspect-square border-2 bg-white/50 backdrop-blur-sm overflow-hidden transition-all duration-700"
              >
                <LayerVisual layerId={layer.id} />
              </motion.div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
