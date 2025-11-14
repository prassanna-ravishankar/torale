import { motion } from "framer-motion";
import { LAYER_CONFIGS } from "@/constants/landing";

// ============================================================================
// TYPES
// ============================================================================

interface SystemDiagramProps {
  activeLayer: number;
}

// ============================================================================
// LAYER VISUAL COMPONENTS
// ============================================================================

/**
 * Foundation: Live Data Grid with flicker animation
 */
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

/**
 * Acquisition: Rising Data Pillars
 */
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

/**
 * Reasoning: Active CPU with tracers
 */
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

/**
 * Signal: Beacon with expanding rings
 */
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

/**
 * Maps layer ID to its visual component
 */
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

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function SystemDiagram({ activeLayer }: SystemDiagramProps) {
  return (
    <div className="w-full max-w-md mx-auto font-mono" style={{ perspective: "1000px" }}>
      {/* Vertically stacked layers with 3D transforms */}
      <div className="relative w-64 h-64 mx-auto" style={{ transformStyle: "preserve-3d" }}>
        {LAYER_CONFIGS.map((layer) => {
          const isActive = activeLayer === layer.id;

          return (
            <motion.div
              key={layer.id}
              animate={{
                opacity: isActive ? 1 : 0.3,
                scale: isActive ? 1.05 : 0.9,
              }}
              className="absolute inset-0 w-64 h-64"
              transition={{ duration: 0.7, ease: "easeInOut" }}
            >
              <motion.div
                style={{
                  transform: `rotateX(60deg) rotateZ(-45deg) translateY(${layer.yOffset}px)`,
                  transformStyle: "preserve-3d",
                }}
                animate={{
                  borderColor: isActive ? "#FF0000" : "#000000",
                }}
                className="w-full h-full border-2 bg-white/50 backdrop-blur-sm overflow-hidden transition-all duration-700"
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
