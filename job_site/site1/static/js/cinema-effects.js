/**
 * LIVIK JOBS - CINEMA 3D EFFECTS & ANIME.JS ENGINE
 * High-performance 3D perspective transforms, physics spring tilt,
 * staggered cascades, rolling HUD counters, and ambient canvas.
 */

(function () {
  'use strict';

  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function initCinemaEngine() {
    if (typeof anime === 'undefined') {
      console.warn('Anime.js not loaded. Retrying in 100ms...');
      setTimeout(initCinemaEngine, 100);
      return;
    }

    if (prefersReducedMotion) {
      console.log('Cinema UI: Reduced motion active. Interactive transforms minimized.');
      initCountersOnly();
      return;
    }

    init3DTilt();
    initZeroGravityFloating();
    initStaggeredEntrances();
    initCinemaCounters();
    initMagneticButtons();
    initAmbientParticleCanvases();
    initFloatingDock();
    initCinemaAmbientOrbs();
  }

  /* --------------------------------------------------------------------------
     1. Interactive 3D Mouse Tilt & Specular Light Reflection
     -------------------------------------------------------------------------- */
  function init3DTilt() {
    const tiltElements = document.querySelectorAll('[data-cinema-tilt], [data-cinema-tilt-3d], .cinema-3d-card');

    tiltElements.forEach(el => {
      // Add dynamic specular shine layer if not present
      if (!el.querySelector('.cinema-card-shine')) {
        const shine = document.createElement('div');
        shine.className = 'cinema-card-shine';
        el.appendChild(shine);
      }

      const shineEl = el.querySelector('.cinema-card-shine');
      const maxTilt = parseFloat(el.getAttribute('data-cinema-max-tilt')) || 12;
      const is3DDeep = el.hasAttribute('data-cinema-tilt-3d');
      const depthChildren = el.querySelectorAll('[data-cinema-depth]');

      let bounds = null;
      let isHovered = false;

      function updateBounds() {
        bounds = el.getBoundingClientRect();
      }

      el.addEventListener('pointerenter', () => {
        isHovered = true;
        updateBounds();
      });

      el.addEventListener('pointermove', (e) => {
        if (!isHovered || !bounds) updateBounds();
        const mouseX = e.clientX - bounds.left;
        const mouseY = e.clientY - bounds.top;

        const px = (mouseX / bounds.width) - 0.5;
        const py = (mouseY / bounds.height) - 0.5;

        const rotX = -py * maxTilt;
        const rotY = px * maxTilt;

        // Apply smooth perspective tilt with Anime.js
        anime.remove(el);
        anime({
          targets: el,
          rotateX: rotX,
          rotateY: rotY,
          scale: 1.02,
          duration: 140,
          easing: 'easeOutQuad'
        });

        // Update specular shine spot
        if (shineEl) {
          const shineX = (px + 0.5) * 100;
          const shineY = (py + 0.5) * 100;
          shineEl.style.background = `radial-gradient(circle at ${shineX}% ${shineY}%, rgba(255, 255, 255, 0.24) 0%, transparent 65%)`;
        }

        // Parallax inner 3D depth layers
        if (depthChildren.length > 0) {
          depthChildren.forEach(child => {
            const depth = parseFloat(child.getAttribute('data-cinema-depth')) || 20;
            const shiftX = px * (depth * 0.4);
            const shiftY = py * (depth * 0.4);
            child.style.transform = `translateZ(${depth}px) translateX(${shiftX}px) translateY(${shiftY}px)`;
          });
        }
      });

      el.addEventListener('pointerleave', () => {
        isHovered = false;
        anime.remove(el);
        anime({
          targets: el,
          rotateX: 0,
          rotateY: 0,
          scale: 1,
          duration: 900,
          easing: 'easeOutElastic(1, .6)'
        });

        if (depthChildren.length > 0) {
          depthChildren.forEach(child => {
            child.style.transform = '';
          });
        }
      });
    });
  }

  /* --------------------------------------------------------------------------
     2. Zero-Gravity 3D Floating Oscillations
     -------------------------------------------------------------------------- */
  function initZeroGravityFloating() {
    const floaters = document.querySelectorAll('[data-cinema-float]');

    floaters.forEach((el, index) => {
      const distance = parseFloat(el.getAttribute('data-cinema-float-dist')) || 9;
      const duration = 2800 + (index * 420) + Math.random() * 600;
      const rot = 2.5 + Math.random() * 2;

      anime({
        targets: el,
        translateY: [-distance, distance],
        rotateZ: [-rot, rot],
        rotateX: [-rot * 0.7, rot * 0.7],
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine',
        duration: duration,
        delay: index * 200
      });
    });
  }

  /* --------------------------------------------------------------------------
     3. Staggered 3D Cascade Entrances
     -------------------------------------------------------------------------- */
  function initStaggeredEntrances() {
    const containers = document.querySelectorAll('[data-cinema-stagger]');

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const container = entry.target;
          observer.unobserve(container);

          const items = container.querySelectorAll('.cinema-stagger-item, .post-bx, .city-bx, .icon-bx-wraper, .card-style-1, .cinema-bento-card');
          if (items.length === 0) return;

          anime({
            targets: items,
            opacity: [0, 1],
            translateY: [40, 0],
            rotateX: [12, 0],
            scale: [0.95, 1],
            delay: anime.stagger(65, { start: 100 }),
            duration: 850,
            easing: 'easeOutCubic'
          });
        }
      });
    }, { threshold: 0.1 });

    containers.forEach(c => observer.observe(c));
  }

  /* --------------------------------------------------------------------------
     4. Cinema HUD Rolling Counters
     -------------------------------------------------------------------------- */
  function initCinemaCounters() {
    const counters = document.querySelectorAll('[data-cinema-counter], .head-counter-bx .counter');

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          observer.unobserve(el);

          const rawText = el.getAttribute('data-target') || el.textContent.trim();
          const targetNum = parseFloat(rawText.replace(/[^0-9.]/g, '')) || 0;
          const prefix = rawText.match(/^[^0-9.]+/)?.[0] || '';
          const suffix = rawText.match(/[^0-9.]+$/)?.[0] || '';

          if (targetNum === 0) return;

          const counterObj = { val: 0 };
          anime({
            targets: counterObj,
            val: targetNum,
            round: 1,
            duration: 1800,
            easing: 'easeOutExpo',
            update: () => {
              const formatted = counterObj.val >= 1000 ? counterObj.val.toLocaleString() : counterObj.val;
              el.textContent = `${prefix}${formatted}${suffix}`;
            }
          });
        }
      });
    }, { threshold: 0.2 });

    counters.forEach(c => observer.observe(c));
  }

  function initCountersOnly() {
    const counters = document.querySelectorAll('[data-cinema-counter]');
    counters.forEach(el => {
      const val = el.getAttribute('data-target') || el.textContent.trim();
      el.textContent = val;
    });
  }

  /* --------------------------------------------------------------------------
     5. Magnetic Button Physics
     -------------------------------------------------------------------------- */
  function initMagneticButtons() {
    const buttons = document.querySelectorAll('[data-cinema-magnetic]');

    buttons.forEach(btn => {
      let rect = null;

      btn.addEventListener('pointerenter', () => {
        rect = btn.getBoundingClientRect();
      });

      btn.addEventListener('pointermove', (e) => {
        if (!rect) rect = btn.getBoundingClientRect();
        const x = (e.clientX - rect.left) - (rect.width / 2);
        const y = (e.clientY - rect.top) - (rect.height / 2);

        anime({
          targets: btn,
          translateX: x * 0.35,
          translateY: y * 0.35,
          duration: 150,
          easing: 'easeOutQuad'
        });
      });

      btn.addEventListener('pointerleave', () => {
        anime({
          targets: btn,
          translateX: 0,
          translateY: 0,
          duration: 700,
          easing: 'easeOutElastic(1, .5)'
        });
      });
    });
  }

  /* --------------------------------------------------------------------------
     6. Ambient Cinema Particle Canvas
     -------------------------------------------------------------------------- */
  function initAmbientParticleCanvases() {
    const canvases = document.querySelectorAll('.cinema-particle-canvas');
    if (canvases.length === 0) return;

    canvases.forEach(canvas => {
      const ctx = canvas.getContext('2d');
      let width = canvas.width = canvas.parentElement.offsetWidth || window.innerWidth;
      let height = canvas.height = canvas.parentElement.offsetHeight || 500;

      window.addEventListener('resize', () => {
        width = canvas.width = canvas.parentElement.offsetWidth || window.innerWidth;
        height = canvas.height = canvas.parentElement.offsetHeight || 500;
      });

      const particleCount = Math.min(Math.floor(width / 28), 55);
      const particles = [];

      for (let i = 0; i < particleCount; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          radius: Math.random() * 2 + 1,
          vx: (Math.random() - 0.5) * 0.45,
          vy: (Math.random() - 0.5) * 0.45,
          color: Math.random() > 0.5 ? 'rgba(0, 242, 254,' : 'rgba(99, 102, 241,',
          alpha: Math.random() * 0.5 + 0.2
        });
      }

      let animId;
      function render() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
          const p = particles[i];
          p.x += p.vx;
          p.y += p.vy;

          if (p.x < 0) p.x = width;
          if (p.x > width) p.x = 0;
          if (p.y < 0) p.y = height;
          if (p.y > height) p.y = 0;

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fillStyle = p.color + p.alpha + ')';
          ctx.fill();

          // Connect adjacent particles
          for (let j = i + 1; j < particles.length; j++) {
            const p2 = particles[j];
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 110) {
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.strokeStyle = `rgba(165, 180, 252, ${0.12 * (1 - dist / 110)})`;
              ctx.lineWidth = 0.8;
              ctx.stroke();
            }
          }
        }

        animId = requestAnimationFrame(render);
      }

      render();
    });
  }

  /* --------------------------------------------------------------------------
     7. Floating Command Dock Interactivity
     -------------------------------------------------------------------------- */
  function initFloatingDock() {
    const dock = document.querySelector('.cinema-floating-dock');
    if (!dock) return;

    let lastScroll = window.scrollY;

    window.addEventListener('scroll', () => {
      const currentScroll = window.scrollY;
      if (currentScroll > lastScroll && currentScroll > 240) {
        // Scrolling down -> hide slightly
        dock.style.transform = 'translateX(-50%) translateY(120px)';
        dock.style.opacity = '0';
      } else {
        // Scrolling up -> reveal
        dock.style.transform = 'translateX(-50%) translateY(0)';
        dock.style.opacity = '1';
      }
      lastScroll = currentScroll;
    }, { passive: true });
  }

  /* --------------------------------------------------------------------------
     8. Ambient Animated Orbs
     -------------------------------------------------------------------------- */
  function initCinemaAmbientOrbs() {
    const orbs = document.querySelectorAll('.cinema-orb');
    if (orbs.length === 0) return;

    orbs.forEach((orb, i) => {
      anime({
        targets: orb,
        translateX: () => anime.random(-40, 40),
        translateY: () => anime.random(-30, 30),
        scale: [0.9, 1.15],
        duration: 5000 + (i * 1200),
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutQuad'
      });
    });
  }

  // Self-execute once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCinemaEngine);
  } else {
    initCinemaEngine();
  }

  // Expose global controller for dynamic page updates
  window.CinemaUI = {
    refresh: initCinemaEngine,
    tilt: init3DTilt,
    counters: initCinemaCounters
  };
})();

