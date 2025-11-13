import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    let scene: THREE.Scene;
    let camera: THREE.PerspectiveCamera;
    let renderer: THREE.WebGLRenderer;
    let particles: THREE.Points;
    let animationId: number;

    // Determine particle count based on device width
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 3000 : 10000;
    const flowSpeed = 0.01;

    function init() {
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        100
      );
      camera.position.z = 10;

      renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
      });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize(window.innerWidth, window.innerHeight);

      // Particle Geometry
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);

      for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 30; // x
        positions[i * 3 + 1] = (Math.random() - 0.5) * 30; // y
        positions[i * 3 + 2] = (Math.random() - 0.5) * 30; // z
      }
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      // Particle Material (Glowing Red)
      const material = new THREE.PointsMaterial({
        color: 0xff0000,
        size: 0.025,
        blending: THREE.AdditiveBlending,
        transparent: true,
        opacity: 1.0,
      });

      particles = new THREE.Points(geometry, material);
      scene.add(particles);
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
      animationId = requestAnimationFrame(animate);

      // Animate particles
      const positions = (particles.geometry.attributes.position as THREE.BufferAttribute).array as Float32Array;
      for (let i = 0; i < particleCount; i++) {
        // Move particle towards the camera
        positions[i * 3 + 2] += flowSpeed;

        // If particle passes camera, reset its position
        if (positions[i * 3 + 2] > camera.position.z) {
          positions[i * 3] = (Math.random() - 0.5) * 30; // x
          positions[i * 3 + 1] = (Math.random() - 0.5) * 30; // y
          positions[i * 3 + 2] = -15; // Reset back
        }
      }
      particles.geometry.attributes.position.needsUpdate = true;

      // Rotate the whole system slightly for more dynamism
      particles.rotation.y += 0.0001;
      particles.rotation.x += 0.0001;

      renderer.render(scene, camera);
    }

    // Initialize and start animation
    init();
    animate();

    // Add resize listener
    window.addEventListener('resize', onWindowResize, false);

    // Cleanup function
    return () => {
      window.removeEventListener('resize', onWindowResize);
      cancelAnimationFrame(animationId);
      renderer.dispose();
      particles.geometry.dispose();
      (particles.material as THREE.Material).dispose();
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} id="particle-vignette-canvas" />
      <div className="vignette-overlay" />
    </>
  );
}
