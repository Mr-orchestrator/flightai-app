/**
 * Premium Apple-Style Aviation Background
 * Sophisticated full-page background with flight route aesthetics
 */

'use client';

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface FlightRoute {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  progress: number;
  speed: number;
  opacity: number;
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const routesRef = useRef<FlightRoute[]>([]);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const timeRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas to full viewport
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize flight routes (connecting major cities)
    const initRoutes = () => {
      routesRef.current = [];
      const routeCount = 12;

      for (let i = 0; i < routeCount; i++) {
        routesRef.current.push({
          startX: Math.random() * canvas.width,
          startY: Math.random() * canvas.height,
          endX: Math.random() * canvas.width,
          endY: Math.random() * canvas.height,
          progress: Math.random(),
          speed: Math.random() * 0.001 + 0.0005,
          opacity: Math.random() * 0.15 + 0.05,
        });
      }
    };
    initRoutes();

    // Draw curved flight path
    const drawFlightPath = (
      startX: number,
      startY: number,
      endX: number,
      endY: number,
      progress: number,
      opacity: number
    ) => {
      const midX = (startX + endX) / 2;
      const midY = (startY + endY) / 2 - 100; // Arc upward

      // Draw full route (very subtle)
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.quadraticCurveTo(midX, midY, endX, endY);
      ctx.strokeStyle = `rgba(249, 178, 51, ${opacity * 0.3})`;
      ctx.lineWidth = 1;
      ctx.setLineDash([10, 15]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Animated dot traveling along path
      const t = progress;
      const dotX = Math.pow(1 - t, 2) * startX + 2 * (1 - t) * t * midX + Math.pow(t, 2) * endX;
      const dotY = Math.pow(1 - t, 2) * startY + 2 * (1 - t) * t * midY + Math.pow(t, 2) * endY;

      // Glowing dot
      const gradient = ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, 8);
      gradient.addColorStop(0, `rgba(249, 178, 51, ${opacity * 2})`);
      gradient.addColorStop(0.5, `rgba(249, 178, 51, ${opacity})`);
      gradient.addColorStop(1, 'rgba(249, 178, 51, 0)');

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(dotX, dotY, 8, 0, Math.PI * 2);
      ctx.fill();
    };

    // Animation loop
    const animate = () => {
      timeRef.current += 0.01;

      // Clear canvas (no trail)
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update and draw routes
      routesRef.current.forEach((route) => {
        route.progress += route.speed;
        if (route.progress > 1) {
          route.progress = 0;
        }

        drawFlightPath(
          route.startX,
          route.startY,
          route.endX,
          route.endY,
          route.progress,
          route.opacity
        );
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden w-screen h-screen">
      {/* Primary Gradient - Apple Style */}
      <motion.div
        className="absolute inset-0 w-full h-full"
        style={{
          background: 'linear-gradient(180deg, #000814 0%, #001d3d 25%, #003566 50%, #001d3d 75%, #000814 100%)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 2 }}
      />

      {/* Mesh Gradient Overlay - Premium Feel */}
      <div
        className="absolute inset-0 w-full h-full"
        style={{
          background: `
            radial-gradient(circle at 20% 20%, rgba(249, 178, 51, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(0, 119, 182, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(5, 22, 77, 0.15) 0%, transparent 70%)
          `,
        }}
      />

      {/* Flight Routes Canvas - Full Coverage */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ width: '100vw', height: '100vh' }}
      />

      {/* Subtle Noise Texture - Apple Style */}
      <div
        className="absolute inset-0 w-full h-full opacity-[0.03] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='4' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' /%3E%3C/svg%3E")`,
        }}
      />

      {/* Animated Glow Orbs - Atmospheric */}
      <motion.div
        className="absolute top-1/4 left-1/3 w-[600px] h-[600px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(249, 178, 51, 0.15) 0%, transparent 70%)',
          filter: 'blur(80px)',
        }}
        animate={{
          scale: [1, 1.1, 1],
          x: [0, 30, 0],
          y: [0, -20, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      <motion.div
        className="absolute bottom-1/3 right-1/4 w-[500px] h-[500px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(0, 119, 182, 0.12) 0%, transparent 70%)',
          filter: 'blur(90px)',
        }}
        animate={{
          scale: [1, 1.15, 1],
          x: [0, -40, 0],
          y: [0, 30, 0],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 3,
        }}
      />

      {/* Vignette Effect - Focus Center */}
      <div
        className="absolute inset-0 w-full h-full"
        style={{
          background: 'radial-gradient(circle at 50% 50%, transparent 0%, rgba(0, 8, 20, 0.4) 100%)',
        }}
      />
    </div>
  );
}
