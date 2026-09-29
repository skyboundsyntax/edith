import React, { useEffect, useRef } from 'react';

/**
 * Animated Ethereal Bokeh Background for EDITH Glassmorphism UI.
 * Matches user reference image:
 * 1. Deeply blurred, dark ambient atmosphere ("less of background, make the background more of a blur")
 * 2. Warm golden/amber optical bokeh orbs floating gently behind glowing glass panels.
 */
export default function FirefliesBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      if (prefersReducedMotion) {
        paintStaticScene();
      }
    };

    window.addEventListener('resize', handleResize);

    // Warm golden & amber bokeh colors matching reference screenshot
    const BOKEH_PALETTE = [
      { r: 251, g: 191, b: 36,  baseAlpha: 0.65 }, // Warm Gold (#fbbf24)
      { r: 245, g: 158, b: 11,  baseAlpha: 0.60 }, // Amber (#f59e0b)
      { r: 254, g: 240, b: 138, baseAlpha: 0.75 }, // Luminous Soft Gold (#fef08a)
      { r: 217, g: 119, b: 6,   baseAlpha: 0.50 }, // Deep Golden Bronze (#d97706)
      { r: 253, g: 224, b: 71,  baseAlpha: 0.70 }  // Solar Gold (#fde047)
    ];

    // Multi-depth bokeh particles matching screenshot distribution
    const PARTICLE_COUNT = Math.min(52, Math.max(30, Math.floor((width * height) / 25000)));
    const particles = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const paletteItem = BOKEH_PALETTE[Math.floor(Math.random() * BOKEH_PALETTE.length)];
      // Varied bokeh disc sizes: from small 8px to large 40px soft lenses
      const isLarge = Math.random() < 0.25;
      const radius = isLarge ? Math.random() * 20 + 20 : Math.random() * 12 + 7;

      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius,
        color: paletteItem,
        alpha: Math.random() * 0.4 + 0.25,
        targetAlpha: Math.random() * 0.4 + 0.3,
        alphaSpeed: (Math.random() * 0.006 + 0.003) * (Math.random() < 0.5 ? 1 : -1),
        vx: (Math.random() - 0.5) * 0.22,
        vy: -Math.random() * 0.35 - 0.08,
        oscillationSpeed: Math.random() * 0.012 + 0.005,
        oscillationAngle: Math.random() * Math.PI * 2,
        oscillationAmp: Math.random() * 2.2 + 0.8
      });
    }

    const paintStaticScene = () => {
      ctx.clearRect(0, 0, width, height);
    };

    if (prefersReducedMotion) {
      paintStaticScene();
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }

    let isTabVisible = true;
    const handleVisibilityChange = () => {
      isTabVisible = !document.hidden;
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Main Bokeh Render Loop - Transparent canvas over blurred CSS backdrop
    const render = () => {
      if (!isTabVisible) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      // Clear transparently - do NOT draw opaque rectangle over page!
      ctx.clearRect(0, 0, width, height);

      // Render floating warm golden bokeh discs
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Soft breathing alpha animation
        p.alpha += p.alphaSpeed;
        if (p.alpha > 0.78) {
          p.alpha = 0.78;
          p.alphaSpeed = -Math.abs(p.alphaSpeed);
        } else if (p.alpha < 0.18) {
          p.alpha = 0.18;
          p.alphaSpeed = Math.abs(p.alphaSpeed);
        }

        // Horizontal sinusoidal drift
        p.oscillationAngle += p.oscillationSpeed;
        const driftX = Math.sin(p.oscillationAngle) * p.oscillationAmp;

        p.x += p.vx + driftX;
        p.y += p.vy;

        // Smooth wrapping
        if (p.y < -60) {
          p.y = height + 50;
          p.x = Math.random() * width;
        } else if (p.y > height + 60) {
          p.y = -50;
          p.x = Math.random() * width;
        }

        if (p.x < -60) {
          p.x = width + 50;
        } else if (p.x > width + 60) {
          p.x = -50;
        }

        // Realistic camera optical bokeh gradient
        const bokehGrad = ctx.createRadialGradient(
          p.x, p.y, 0,
          p.x, p.y, p.radius
        );
        bokehGrad.addColorStop(0, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.95})`);
        bokehGrad.addColorStop(0.5, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.65})`);
        bokehGrad.addColorStop(0.85, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.25})`);
        bokehGrad.addColorStop(1, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, 0)`);

        ctx.fillStyle = bokehGrad;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        // Luminous optical core for medium/large bokeh discs
        if (p.radius > 14) {
          const coreGrad = ctx.createRadialGradient(
            p.x, p.y, 0,
            p.x, p.y, p.radius * 0.45
          );
          coreGrad.addColorStop(0, `rgba(255, 255, 255, ${p.alpha * 0.85})`);
          coreGrad.addColorStop(0.5, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.alpha * 0.45})`);
          coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
          ctx.fillStyle = coreGrad;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius * 0.45, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return (
    <>
      {/* 1. Deep Blurred Ambient Architectural Background Layer */}
      <div
        className="edith-ambient-blurred-backdrop"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 0,
          pointerEvents: 'none',
          background: `
            radial-gradient(ellipse 90% 70% at 50% 35%, rgba(16, 36, 62, 0.65) 0%, transparent 70%),
            radial-gradient(circle at 15% 25%, rgba(20, 48, 80, 0.45) 0%, transparent 50%),
            radial-gradient(circle at 85% 65%, rgba(18, 42, 72, 0.4) 0%, transparent 55%),
            linear-gradient(180deg, #050d18 0%, #081628 50%, #030811 100%)
          `,
          filter: 'blur(36px)',
          WebkitFilter: 'blur(36px)',
          transform: 'scale(1.05)'
        }}
        aria-hidden="true"
      />

      {/* 2. Floating Golden Bokeh Discs Canvas (strictly non-blocking background) */}
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

      {/* 3. Subtle Dark Vignette for Cinematic Depth */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          pointerEvents: 'none',
          zIndex: 0,
          background: 'radial-gradient(circle at 50% 45%, transparent 40%, rgba(2, 6, 12, 0.55) 100%)'
        }}
        aria-hidden="true"
      />
    </>
  );
}
