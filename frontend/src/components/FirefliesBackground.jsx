import React, { useEffect, useRef } from 'react';

/**
 * Animated Fireflies Background for EDITH Glassmorphic UI.
 * Minimal & Restrained: Smooth, low-overhead particle field of drifting,
 * glowing fireflies that float smoothly behind the frosted glass interface layers.
 * Fully respects prefers-reduced-motion and tab visibility.
 */
export default function FirefliesBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mouse coordinates with smoothing
    const mouse = {
      x: width / 2,
      y: height / 2,
      targetX: width / 2,
      targetY: height / 2,
      active: false
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      if (prefersReducedMotion) {
        paintStaticScene();
      }
    };

    const handleMouseMove = (e) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
      mouse.active = true;
    };

    const handleMouseLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    // Curated color palette matching the screenshot
    const GLOW_COLORS = [
      { r: 56, g: 189, b: 248 },  // Electric Cyan (#38bdf8)
      { r: 45, g: 212, b: 191 },  // Neon Teal (#2dd4bf)
      { r: 14, g: 165, b: 233 },  // Deep Sky Blue (#0ea5e9)
      { r: 99, g: 102, b: 241 },  // Indigo Glow (#6366f1)
      { r: 253, g: 224, b: 71 }   // Warm Golden Firefly (#fde047)
    ];

    // Minimal & restrained particle count (28-36) for 60fps & zero battery drain
    const PARTICLE_COUNT = Math.min(32, Math.max(16, Math.floor((width * height) / 32000)));
    const particles = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const color = GLOW_COLORS[Math.floor(Math.random() * GLOW_COLORS.length)];
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        baseRadius: Math.random() * 1.8 + 1.2,
        color,
        alpha: Math.random() * 0.55 + 0.25,
        alphaSpeed: (Math.random() * 0.008 + 0.004) * (Math.random() < 0.5 ? 1 : -1),
        vx: (Math.random() - 0.5) * 0.35,
        vy: -Math.random() * 0.35 - 0.1, // Smooth gentle drift
        oscillationSpeed: Math.random() * 0.015 + 0.008,
        oscillationAngle: Math.random() * Math.PI * 2,
        oscillationAmp: Math.random() * 1.0 + 0.5,
        glowMultiplier: Math.random() * 4 + 3.5
      });
    }

    const paintStaticScene = () => {
      ctx.clearRect(0, 0, width, height);
      const bgGrad = ctx.createRadialGradient(
        width * 0.45, height * 0.35, 50,
        width * 0.5, height * 0.5, Math.max(width, height) * 0.85
      );
      bgGrad.addColorStop(0, '#0c162c');
      bgGrad.addColorStop(0.45, '#070d1a');
      bgGrad.addColorStop(1, '#04070e');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);
    };

    if (prefersReducedMotion) {
      paintStaticScene();
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseleave', handleMouseLeave);
      };
    }

    let isTabVisible = true;
    const handleVisibilityChange = () => {
      isTabVisible = !document.hidden;
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Animation Loop
    const render = () => {
      if (!isTabVisible) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      // Smooth mouse easing
      if (mouse.active) {
        mouse.x += (mouse.targetX - mouse.x) * 0.04;
        mouse.y += (mouse.targetY - mouse.y) * 0.04;
      }

      ctx.clearRect(0, 0, width, height);

      // Deep space atmospheric base
      const bgGrad = ctx.createRadialGradient(
        width * 0.45,
        height * 0.35,
        50,
        width * 0.5,
        height * 0.5,
        Math.max(width, height) * 0.85
      );
      bgGrad.addColorStop(0, '#0c162c');
      bgGrad.addColorStop(0.45, '#070d1a');
      bgGrad.addColorStop(1, '#04070e');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // Render each restrained glowing firefly
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Pulsating alpha (glow breathing)
        p.alpha += p.alphaSpeed;
        if (p.alpha > 0.85) {
          p.alpha = 0.85;
          p.alphaSpeed = -Math.abs(p.alphaSpeed);
        } else if (p.alpha < 0.2) {
          p.alpha = 0.2;
          p.alphaSpeed = Math.abs(p.alphaSpeed);
        }

        // Sine wave horizontal drift
        p.oscillationAngle += p.oscillationSpeed;
        const driftX = Math.sin(p.oscillationAngle) * p.oscillationAmp;

        p.x += p.vx + driftX;
        p.y += p.vy;

        // Subtle mouse repulsion
        if (mouse.active) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120 && dist > 0) {
            const force = (120 - dist) / 120;
            p.x -= (dx / dist) * force * 0.45;
            p.y -= (dy / dist) * force * 0.45;
          }
        }

        // Screen wrap-around with smooth re-entry
        if (p.y < -30) {
          p.y = height + 20;
          p.x = Math.random() * width;
        } else if (p.y > height + 30) {
          p.y = -20;
          p.x = Math.random() * width;
        }

        if (p.x < -30) {
          p.x = width + 20;
        } else if (p.x > width + 30) {
          p.x = -20;
        }

        // Outer soft glow halo
        const haloRadius = Math.max(6, p.baseRadius * p.glowMultiplier);
        const glowGrad = ctx.createRadialGradient(
          p.x, p.y, 0,
          p.x, p.y, haloRadius
        );
        glowGrad.addColorStop(0, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.8})`);
        glowGrad.addColorStop(0.4, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.28})`);
        glowGrad.addColorStop(1, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, 0)`);

        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(p.x, p.y, haloRadius, 0, Math.PI * 2);
        ctx.fill();

        // Bright inner core
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(1, p.alpha * 1.1)})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.baseRadius * 0.7, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0
      }}
      aria-hidden="true"
    />
  );
}
