import React, { useRef, useEffect } from "react";

export default function SkyBackground() {
  const ref = useRef(null);

  useEffect(() => {
    const factor = 0.15; // smooth, seamless parallax drift factor
    let ticking = false;

    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          if (ref.current) {
            // Translate upwards smoothly as user scrolls down, strictly bounded to prevent any out-of-view gaps
            const maxTranslate = window.innerHeight * 0.20;
            const shift = Math.min(window.scrollY * factor, maxTranslate);
            ref.current.style.transform = `translate3d(0, -${shift}px, 0)`;
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return <div ref={ref} className="parallax-sky-bg" />;
}
