import { useEffect, useRef } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number; // velocity x
  vy: number; // velocity y
  connections: Node[];
}

interface AnimatedBackgroundProps {
  className?: string;
}

export function AnimatedBackground({ className = '' }: AnimatedBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Disable animation on mobile devices
    const isMobile = window.innerWidth < 768;
    if (isMobile) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Configuration - adapted to Torale color palette
    const NUM_NODES = 50;
    const NODE_RADIUS = 3;
    const NODE_SPEED = 0.15; // Slow movement speed
    const CONNECTION_DISTANCE_THRESHOLD = 200;
    const NODE_COLOR = 'rgba(3, 2, 19, 0.3)'; // Primary color, darker
    const LINE_COLOR = 'rgba(3, 2, 19, 0.15)'; // Darker lines
    const GLOW_COLOR = {
      inner: [100, 150, 255], // Bright blue glow core
      outerStart: [120, 170, 255], // Medium blue
      outerMid: [80, 130, 255],
      outerEnd: [60, 100, 220]
    };
    const GLOW_RADIUS = 25;
    const GLOW_SIZE_GROWTH = 1.0; // 100% size increase on glow (2x)

    // Animation timing
    const FADE_DURATION = 1600; // 2x slower fade
    const PAUSE_DURATION = 2500; // 2.5x longer pause
    const TRANSITION_DELAY = 400; // 2x longer delay

    // State variables
    let nodes: Node[] = [];
    const dpr = window.devicePixelRatio || 1;
    let canvasWidth: number, canvasHeight: number;

    let currentNode: Node | null = null;
    let previousNode: Node | null = null;

    let timeInState = 0;
    let lastTimestamp = 0;
    let animationPhase: 'PAUSED_ON_CURRENT' | 'FADE_IN_OUT' = 'PAUSED_ON_CURRENT';
    let animationFrameId: number;

    function resizeCanvas() {
      const rect = canvas.getBoundingClientRect();
      canvasWidth = rect.width;
      canvasHeight = rect.height;

      canvas.width = canvasWidth * dpr;
      canvas.height = canvasHeight * dpr;

      ctx.scale(dpr, dpr);
    }

    function createNodes() {
      nodes = [];
      for (let i = 0; i < NUM_NODES; i++) {
        nodes.push({
          x: Math.random() * canvasWidth,
          y: Math.random() * canvasHeight,
          vx: (Math.random() - 0.5) * NODE_SPEED,
          vy: (Math.random() - 0.5) * NODE_SPEED,
          connections: []
        });
      }
    }

    function createConnections() {
      for (let i = 0; i < nodes.length; i++) {
        nodes[i].connections = [];
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeA = nodes[i];
          const nodeB = nodes[j];

          const dx = nodeA.x - nodeB.x;
          const dy = nodeA.y - nodeB.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < CONNECTION_DISTANCE_THRESHOLD) {
            nodeA.connections.push(nodeB);
            nodeB.connections.push(nodeA);
          }
        }
      }
    }

    function pickNextNode() {
      previousNode = currentNode;

      let randomIndex;
      let selectedNode;

      do {
        randomIndex = Math.floor(Math.random() * nodes.length);
        selectedNode = nodes[randomIndex];
      } while (nodes.length > 1 && selectedNode === previousNode);

      currentNode = selectedNode;

      animationPhase = 'FADE_IN_OUT';
      timeInState = 0;
    }

    function drawLines() {
      ctx.strokeStyle = LINE_COLOR;
      ctx.lineWidth = 1;
      const drawnConnections = new Set<string>();

      for (const node of nodes) {
        for (const neighbor of node.connections) {
          const id1 = nodes.indexOf(node);
          const id2 = nodes.indexOf(neighbor);
          const key = id1 < id2 ? `${id1}-${id2}` : `${id2}-${id1}`;

          if (!drawnConnections.has(key)) {
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(neighbor.x, neighbor.y);
            ctx.stroke();
            drawnConnections.add(key);
          }
        }
      }
    }

    function drawNodes() {
      ctx.fillStyle = NODE_COLOR;
      for (const node of nodes) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, NODE_RADIUS, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function drawGlow(x: number, y: number, alpha: number) {
      if (alpha <= 0) return;

      // Calculate size growth based on alpha
      const sizeMultiplier = 1 + (GLOW_SIZE_GROWTH * alpha);
      const glowRadius = GLOW_RADIUS * sizeMultiplier;
      const nodeRadius = NODE_RADIUS * sizeMultiplier;

      const innerColor = `rgba(${GLOW_COLOR.inner[0]}, ${GLOW_COLOR.inner[1]}, ${GLOW_COLOR.inner[2]}, ${alpha * 0.5})`;
      const gradientStart = `rgba(${GLOW_COLOR.outerStart[0]}, ${GLOW_COLOR.outerStart[1]}, ${GLOW_COLOR.outerStart[2]}, ${alpha * 0.4})`;
      const gradientMid = `rgba(${GLOW_COLOR.outerMid[0]}, ${GLOW_COLOR.outerMid[1]}, ${GLOW_COLOR.outerMid[2]}, ${alpha * 0.2})`;
      const gradientEnd = `rgba(${GLOW_COLOR.outerEnd[0]}, ${GLOW_COLOR.outerEnd[1]}, ${GLOW_COLOR.outerEnd[2]}, 0)`;

      // Outer gradient glow
      const gradient = ctx.createRadialGradient(x, y, nodeRadius * 0.5, x, y, glowRadius);
      gradient.addColorStop(0, gradientStart);
      gradient.addColorStop(0.3, gradientMid);
      gradient.addColorStop(1, gradientEnd);

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
      ctx.fill();

      // Highlighted inner node
      ctx.fillStyle = innerColor;
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
      ctx.fill();
    }

    function easeInOutSine(x: number): number {
      return -(Math.cos(Math.PI * x) - 1) / 2;
    }

    function drawVignette() {
      // Create radial gradient for vignette effect (20-30% fade at edges)
      const centerX = canvasWidth / 2;
      const centerY = canvasHeight / 2;
      const maxRadius = Math.max(canvasWidth, canvasHeight) * 0.8;

      const vignette = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius);
      vignette.addColorStop(0, 'rgba(255, 255, 255, 0)'); // Transparent center
      vignette.addColorStop(0.7, 'rgba(255, 255, 255, 0)'); // Start fading
      vignette.addColorStop(1, 'rgba(255, 255, 255, 0.25)'); // 25% white at edges (subtle fade)

      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    }

    function updateNodePositions() {
      // Update node positions and handle edge wrapping
      for (const node of nodes) {
        node.x += node.vx;
        node.y += node.vy;

        // Wrap around edges
        if (node.x < 0) node.x = canvasWidth;
        if (node.x > canvasWidth) node.x = 0;
        if (node.y < 0) node.y = canvasHeight;
        if (node.y > canvasHeight) node.y = 0;
      }

      // Update connections based on new positions
      createConnections();
    }

    function animate(timestamp: number) {
      const deltaTime = timestamp - (lastTimestamp || timestamp);
      lastTimestamp = timestamp;
      timeInState += deltaTime;

      // Update node positions
      updateNodePositions();

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.restore();

      drawLines();
      drawNodes();

      let currentAlpha = 0;
      let previousAlpha = 0;

      switch (animationPhase) {
        case 'PAUSED_ON_CURRENT': {
          currentAlpha = 1;
          if (timeInState > PAUSE_DURATION) {
            pickNextNode();
          }
          break;
        }
        case 'FADE_IN_OUT': {
          const fadeOutProgress = Math.min(1, timeInState / FADE_DURATION);
          previousAlpha = 1 - easeInOutSine(fadeOutProgress);

          let fadeInProgress = 0;
          if (timeInState > TRANSITION_DELAY) {
            fadeInProgress = Math.min(1, (timeInState - TRANSITION_DELAY) / FADE_DURATION);
            currentAlpha = easeInOutSine(fadeInProgress);
          } else {
            currentAlpha = 0;
          }

          if (fadeOutProgress >= 1 && fadeInProgress >= 1) {
            animationPhase = 'PAUSED_ON_CURRENT';
            timeInState = 0;
          }
          break;
        }
      }

      // Draw glows
      if (previousNode && previousAlpha > 0) {
        drawGlow(previousNode.x, previousNode.y, previousAlpha);
      }
      if (currentNode && currentAlpha > 0) {
        drawGlow(currentNode.x, currentNode.y, currentAlpha);
      }

      // Apply vignette effect
      drawVignette();

      animationFrameId = requestAnimationFrame(animate);
    }

    function init() {
      createNodes();
      createConnections();

      currentNode = null;
      previousNode = null;

      pickNextNode();

      animationPhase = 'FADE_IN_OUT';
      timeInState = TRANSITION_DELAY;
    }

    const handleResize = () => {
      resizeCanvas();
      init();
    };

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!prefersReducedMotion) {
      resizeCanvas();
      init();
      animationFrameId = requestAnimationFrame(animate);

      window.addEventListener('resize', handleResize);
    }

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full ${className}`}
    />
  );
}
