import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface FirstTimeExperienceProps {
  onComplete: () => void
}

export function FirstTimeExperience({ onComplete }: FirstTimeExperienceProps) {
  const [step, setStep] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)

  const SILKY_EASE = [0.16, 1, 0.3, 1] as const

  // Auto-advance for steps 0-3
  useEffect(() => {
    const durations = [6000, 3500, 3500, 3500] // Extended Step 0 for 'ceremony'
    if (step < 4 && durations[step]) {
      const timer = setTimeout(() => {
        if (isAnimating) return
        handleNext()
      }, durations[step])
      return () => clearTimeout(timer)
    }
  }, [step, isAnimating])

  const handleNext = () => {
    if (isAnimating || step >= 4) return
    setIsAnimating(true)
    setStep((prev) => Math.min(prev + 1, 4))
    setTimeout(() => setIsAnimating(false), 800)
  }

  const handleDotClick = (targetStep: number) => {
    if (isAnimating || targetStep === step) return
    setIsAnimating(true)
    setStep(targetStep)
    setTimeout(() => setIsAnimating(false), 800)
  }

  const handleComplete = () => {
    onComplete()
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-[#fafafa]">
      {/* Arc-inspired Mesh Gradient Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div 
          animate={{
            scale: [1, 1.2, 1],
            x: [0, 50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] bg-brand-orange/15 blur-[120px] rounded-full"
        />
        <motion.div 
          animate={{
            scale: [1, 1.1, 1],
            x: [0, -30, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute -bottom-[20%] -right-[10%] w-[60%] h-[60%] bg-zinc-400/10 blur-[100px] rounded-full"
        />
      </div>

      <div className="relative w-full max-w-2xl px-6">
        {/* The "Vessel" - Morphing Container */}
        <motion.div 
          layout
          transition={{ 
            layout: { duration: 0.8, ease: SILKY_EASE },
            opacity: { duration: 0.4 }
          }}
          className="relative overflow-hidden bg-white/70 backdrop-blur-2xl border border-white shadow-[0_20px_50px_rgba(0,0,0,0.04)] rounded-[40px]"
        >
          <AnimatePresence mode="popLayout">
            {step === 0 && (
              <motion.div
                key="step-0"
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.04, filter: "blur(12px)", y: -10 }}
                transition={{ duration: 0.8, ease: SILKY_EASE }}
                className="flex flex-col items-center justify-center p-20 space-y-14"
              >
                {/* Search to Bell Animation - Recalibrated for 6s flow */}
                <div className="relative h-32 w-full flex items-center justify-center">
                  <motion.div
                    animate={{
                      opacity: [0, 1, 1, 0],
                      scale: [0.9, 1, 1, 0.9],
                      y: [10, 0, 0, -10],
                    }}
                    transition={{ 
                      duration: 6, 
                      times: [0, 0.1, 0.4, 0.6],
                      ease: "easeInOut"
                    }}
                    className="absolute flex items-center gap-4 bg-white border border-zinc-100 rounded-2xl px-8 py-5 shadow-sm"
                  >
                    <Search className="w-5 h-5 text-zinc-300" />
                    <div className="h-2 w-32 bg-zinc-50 rounded-full" />
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.4, rotate: -15 }}
                    animate={{ 
                      opacity: [0, 0, 1, 1], 
                      scale: [0.4, 0.4, 1.05, 1],
                      rotate: [15, 15, -5, 0],
                    }}
                    transition={{ 
                      duration: 6, 
                      times: [0, 0.45, 0.65, 0.8],
                      ease: SILKY_EASE
                    }}
                    className="absolute bg-brand-orange text-white p-7 rounded-[30px] shadow-2xl shadow-brand-orange/25"
                  >
                    <Bell className="w-14 h-14" />
                  </motion.div>
                </div>

                <div className="text-center space-y-5">
                  <motion.h1 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6, duration: 1, ease: SILKY_EASE }}
                    className="text-5xl font-bold text-zinc-900 font-grotesk tracking-tight leading-[1.1]"
                  >
                    Stop checking.<br />Start knowing.
                  </motion.h1>
                  <motion.p 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1, duration: 1, ease: SILKY_EASE }}
                    className="text-zinc-500 font-sans text-xl"
                  >
                    The machine watches the web so you don't have to.
                  </motion.p>
                </div>
              </motion.div>
            )}

            {step === 1 && (
              <motion.div
                key="step-1"
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.7, ease: SILKY_EASE }}
                className="p-16"
              >
                <div className="space-y-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-orange/10 text-brand-orange text-[10px] font-mono font-bold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 bg-brand-orange rounded-full animate-pulse" />
                    Initialization
                  </div>
                  <h2 className="text-4xl font-bold text-zinc-900 font-grotesk leading-tight">
                    Describe what you're<br />watching for
                  </h2>
                  <p className="text-xl text-zinc-500 font-sans leading-relaxed">
                    Tell Torale what you want to know. <span className="text-zinc-900 font-medium italic">"When does the iPhone 16 launch?"</span> or <span className="text-zinc-900 font-medium italic">"Alert me when tickets for Coachella go on sale."</span>
                  </p>
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step-2"
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.7, ease: SILKY_EASE }}
                className="p-16"
              >
                <div className="space-y-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-600 text-[10px] font-mono font-bold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                    Process
                  </div>
                  <h2 className="text-4xl font-bold text-zinc-900 font-grotesk leading-tight">
                    The machine scans<br />the horizon
                  </h2>
                  <p className="text-xl text-zinc-500 font-sans leading-relaxed">
                    Torale runs searches on your schedule, then uses AI to analyze if your condition is met. Continuous monitoring, zero effort.
                  </p>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step-3"
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.7, ease: SILKY_EASE }}
                className="p-16"
              >
                <div className="space-y-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-600 text-[10px] font-mono font-bold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
                    Delivery
                  </div>
                  <h2 className="text-4xl font-bold text-zinc-900 font-grotesk leading-tight">
                    Get notified when<br />it matters
                  </h2>
                  <p className="text-xl text-zinc-500 font-sans leading-relaxed">
                    When your condition is met, Torale sends you an email or webhook. You stay in the loop without constantly checking.
                  </p>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div
                key="step-4"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, ease: SILKY_EASE }}
                className="p-12 text-center"
              >
                <div className="space-y-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-600 text-[10px] font-mono font-bold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                    System Ready
                  </div>
                  <h2 className="text-4xl font-bold text-zinc-900 font-grotesk leading-tight">
                    The machine is at<br />your command
                  </h2>
                  <div className="relative group">
                    <div className="absolute -inset-4 bg-gradient-to-b from-brand-orange/20 to-transparent opacity-0 group-hover:opacity-100 blur-2xl transition-opacity duration-1000" />
                    <img
                      src="/images/torale-monitor.png"
                      alt="Torale monitor example"
                      className="relative w-full border border-zinc-100 rounded-2xl shadow-2xl"
                    />
                  </div>
                  <Button
                    onClick={handleComplete}
                    size="lg"
                    className="w-full sm:w-auto bg-zinc-900 hover:bg-brand-orange text-white font-bold font-grotesk px-10 py-7 text-lg rounded-2xl shadow-xl hover:shadow-brand-orange/20 transition-all active:scale-[0.98]"
                  >
                    INITIALIZE FIRST MONITOR
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Floating Navigation */}
        <div className="mt-12 flex flex-col items-center gap-8">
          <div className="flex justify-center gap-3">
            {[0, 1, 2, 3, 4].map((dotStep) => (
              <button
                key={dotStep}
                onClick={() => handleDotClick(dotStep)}
                disabled={isAnimating}
                className="relative p-2 group outline-none"
                aria-label={`Go to step ${dotStep}`}
              >
                <div className={`h-1.5 rounded-full transition-all duration-500 ${
                  step === dotStep
                    ? 'w-8 bg-zinc-900'
                    : 'w-1.5 bg-zinc-200 group-hover:bg-zinc-400'
                }`} />
                {step === dotStep && (
                  <motion.div 
                    layoutId="activeIndicator"
                    transition={{ duration: 0.5, ease: SILKY_EASE }}
                    className="absolute inset-0 border border-zinc-900/10 rounded-full"
                  />
                )}
              </button>
            ))}
          </div>
          
          <AnimatePresence>
            {step < 4 && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={handleComplete}
                className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest hover:text-zinc-900 transition-colors flex items-center gap-2 group"
              >
                Skip intro <span className="text-lg transition-transform group-hover:translate-x-1">→</span>
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
