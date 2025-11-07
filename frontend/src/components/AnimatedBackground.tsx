import { useEffect, useRef } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  connections: Node[];
}

interface AnimatedBackgroundProps {
  className?: string;
}

class NetworkAnimation {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private nodes: Node[] = [];
  private currentNode: Node | null = null;
  private previousNode: Node | null = null;
  private timeInState = 0;
  private lastTimestamp = 0;
  private animationPhase: 'PAUSED_ON_CURRENT' | 'FADE_IN_OUT' = 'PAUSED_ON_CURRENT';
  private animationFrameId: number | null = null;
  private canvasWidth = 0;
  private canvasHeight = 0;
  private readonly dpr: number;

  // Configuration
  private readonly NUM_NODES = 50;
  private readonly NODE_RADIUS = 3;
  private readonly NODE_SPEED = 0.15;
  private readonly CONNECTION_DISTANCE_THRESHOLD = 200;
  private readonly NODE_COLOR = 'rgba(3, 2, 19, 0.3)';
  private readonly LINE_COLOR = 'rgba(3, 2, 19, 0.15)';
  private readonly GLOW_COLOR = {
    inner: [100, 150, 255],
    outerStart: [120, 170, 255],
    outerMid: [80, 130, 255],
    outerEnd: [60, 100, 220]
  };
  private readonly GLOW_RADIUS = 25;
  private readonly GLOW_SIZE_GROWTH = 1.0;
  private readonly FADE_DURATION = 1600;
  private readonly PAUSE_DURATION = 2500;
  private readonly TRANSITION_DELAY = 400;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');
    this.ctx = ctx;
    this.dpr = window.devicePixelRatio || 1;

    this.resizeCanvas();
    this.createNodes();
    this.createConnections();
    this.pickNextNode();

    // Start with fade-in
    this.animationPhase = 'FADE_IN_OUT';
    this.timeInState = this.TRANSITION_DELAY;

    window.addEventListener('resize', this.handleResize);
  }

  private handleResize = () => {
    this.resizeCanvas();
    this.createNodes();
    this.createConnections();
  };

  private resizeCanvas() {
    const rect = this.canvas.getBoundingClientRect();
    this.canvasWidth = rect.width;
    this.canvasHeight = rect.height;

    this.canvas.width = this.canvasWidth * this.dpr;
    this.canvas.height = this.canvasHeight * this.dpr;

    this.ctx.scale(this.dpr, this.dpr);
  }

  private createNodes() {
    this.nodes = [];
    for (let i = 0; i < this.NUM_NODES; i++) {
      this.nodes.push({
        x: Math.random() * this.canvasWidth,
        y: Math.random() * this.canvasHeight,
        vx: (Math.random() - 0.5) * this.NODE_SPEED,
        vy: (Math.random() - 0.5) * this.NODE_SPEED,
        connections: []
      });
    }
  }

  private createConnections() {
    for (let i = 0; i < this.nodes.length; i++) {
      this.nodes[i].connections = [];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const nodeA = this.nodes[i];
        const nodeB = this.nodes[j];

        const dx = nodeA.x - nodeB.x;
        const dy = nodeA.y - nodeB.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < this.CONNECTION_DISTANCE_THRESHOLD) {
          nodeA.connections.push(nodeB);
          nodeB.connections.push(nodeA);
        }
      }
    }
  }

  private pickNextNode() {
    this.previousNode = this.currentNode;

    let randomIndex;
    let selectedNode;

    do {
      randomIndex = Math.floor(Math.random() * this.nodes.length);
      selectedNode = this.nodes[randomIndex];
    } while (this.nodes.length > 1 && selectedNode === this.previousNode);

    this.currentNode = selectedNode;

    this.animationPhase = 'FADE_IN_OUT';
    this.timeInState = 0;
  }

  private drawLines() {
    this.ctx.strokeStyle = this.LINE_COLOR;
    this.ctx.lineWidth = 1;
    const drawnConnections = new Set<string>();

    for (const node of this.nodes) {
      for (const neighbor of node.connections) {
        const id1 = this.nodes.indexOf(node);
        const id2 = this.nodes.indexOf(neighbor);
        const key = id1 < id2 ? `${id1}-${id2}` : `${id2}-${id1}`;

        if (!drawnConnections.has(key)) {
          this.ctx.beginPath();
          this.ctx.moveTo(node.x, node.y);
          this.ctx.lineTo(neighbor.x, neighbor.y);
          this.ctx.stroke();
          drawnConnections.add(key);
        }
      }
    }
  }

  private drawNodes() {
    this.ctx.fillStyle = this.NODE_COLOR;
    for (const node of this.nodes) {
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, this.NODE_RADIUS, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  private drawGlow(x: number, y: number, alpha: number) {
    if (alpha <= 0) return;

    const sizeMultiplier = 1 + (this.GLOW_SIZE_GROWTH * alpha);
    const glowRadius = this.GLOW_RADIUS * sizeMultiplier;
    const nodeRadius = this.NODE_RADIUS * sizeMultiplier;

    const innerColor = `rgba(${this.GLOW_COLOR.inner[0]}, ${this.GLOW_COLOR.inner[1]}, ${this.GLOW_COLOR.inner[2]}, ${alpha * 0.5})`;
    const gradientStart = `rgba(${this.GLOW_COLOR.outerStart[0]}, ${this.GLOW_COLOR.outerStart[1]}, ${this.GLOW_COLOR.outerStart[2]}, ${alpha * 0.4})`;
    const gradientMid = `rgba(${this.GLOW_COLOR.outerMid[0]}, ${this.GLOW_COLOR.outerMid[1]}, ${this.GLOW_COLOR.outerMid[2]}, ${alpha * 0.2})`;
    const gradientEnd = `rgba(${this.GLOW_COLOR.outerEnd[0]}, ${this.GLOW_COLOR.outerEnd[1]}, ${this.GLOW_COLOR.outerEnd[2]}, 0)`;

    const gradient = this.ctx.createRadialGradient(x, y, nodeRadius * 0.5, x, y, glowRadius);
    gradient.addColorStop(0, gradientStart);
    gradient.addColorStop(0.3, gradientMid);
    gradient.addColorStop(1, gradientEnd);

    this.ctx.fillStyle = gradient;
    this.ctx.beginPath();
    this.ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.fillStyle = innerColor;
    this.ctx.beginPath();
    this.ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
    this.ctx.fill();
  }

  private easeInOutSine(x: number): number {
    return -(Math.cos(Math.PI * x) - 1) / 2;
  }

  private drawVignette() {
    const centerX = this.canvasWidth / 2;
    const centerY = this.canvasHeight / 2;
    const maxRadius = Math.max(this.canvasWidth, this.canvasHeight) * 0.8;

    const vignette = this.ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius);
    vignette.addColorStop(0, 'rgba(255, 255, 255, 0)');
    vignette.addColorStop(0.7, 'rgba(255, 255, 255, 0)');
    vignette.addColorStop(1, 'rgba(255, 255, 255, 0.25)');

    this.ctx.fillStyle = vignette;
    this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
  }

  private updateNodePositions() {
    for (const node of this.nodes) {
      node.x += node.vx;
      node.y += node.vy;

      if (node.x < 0) node.x = this.canvasWidth;
      if (node.x > this.canvasWidth) node.x = 0;
      if (node.y < 0) node.y = this.canvasHeight;
      if (node.y > this.canvasHeight) node.y = 0;
    }

    this.createConnections();
  }

  private animate = (timestamp: number) => {
    const deltaTime = timestamp - (this.lastTimestamp || timestamp);
    this.lastTimestamp = timestamp;
    this.timeInState += deltaTime;

    this.updateNodePositions();

    this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);

    this.drawLines();
    this.drawNodes();

    let currentAlpha = 0;
    let previousAlpha = 0;

    switch (this.animationPhase) {
      case 'PAUSED_ON_CURRENT': {
        currentAlpha = 1;
        if (this.timeInState > this.PAUSE_DURATION) {
          this.pickNextNode();
        }
        break;
      }
      case 'FADE_IN_OUT': {
        const fadeOutProgress = Math.min(1, this.timeInState / this.FADE_DURATION);
        previousAlpha = 1 - this.easeInOutSine(fadeOutProgress);

        let fadeInProgress = 0;
        if (this.timeInState > this.TRANSITION_DELAY) {
          fadeInProgress = Math.min(1, (this.timeInState - this.TRANSITION_DELAY) / this.FADE_DURATION);
          currentAlpha = this.easeInOutSine(fadeInProgress);
        } else {
          currentAlpha = 0;
        }

        if (fadeOutProgress >= 1 && fadeInProgress >= 1) {
          this.animationPhase = 'PAUSED_ON_CURRENT';
          this.timeInState = 0;
        }
        break;
      }
    }

    if (this.previousNode && previousAlpha > 0) {
      this.drawGlow(this.previousNode.x, this.previousNode.y, previousAlpha);
    }
    if (this.currentNode && currentAlpha > 0) {
      this.drawGlow(this.currentNode.x, this.currentNode.y, currentAlpha);
    }

    this.drawVignette();

    this.animationFrameId = requestAnimationFrame(this.animate);
  };

  start() {
    if (this.animationFrameId === null) {
      this.animationFrameId = requestAnimationFrame(this.animate);
    }
  }

  stop() {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    window.removeEventListener('resize', this.handleResize);
  }
}

export function AnimatedBackground({ className = '' }: AnimatedBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Disable animation on mobile devices
    const isMobile = window.innerWidth < 768;
    if (isMobile) return;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const animation = new NetworkAnimation(canvas);
    animation.start();

    return () => {
      animation.stop();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full ${className}`}
    />
  );
}
