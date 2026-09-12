import { useEffect, useRef, useState } from 'react';

/** Tween diagram coordinates only; numerical readouts keep the exact computed state. */
export function AnimatedVector({
  x,
  y,
  motion,
  duration = 650,
}: {
  x: number;
  y: number;
  motion: boolean;
  duration?: number;
}) {
  const current = useRef({ x, y });
  const [point, setPoint] = useState({ x, y });
  useEffect(() => {
    if (!motion) {
      current.current = { x, y };
      return;
    }
    const from = { ...current.current };
    const start = performance.now();
    let handle = 0;
    const tick = (now: number) => {
      const fraction = Math.min(1, Math.max(0, (now - start) / duration));
      const eased = fraction * fraction * (3 - 2 * fraction);
      current.current = {
        x: from.x + (x - from.x) * eased,
        y: from.y + (y - from.y) * eased,
      };
      setPoint(current.current);
      if (fraction < 1) handle = requestAnimationFrame(tick);
    };
    handle = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(handle);
  }, [x, y, motion, duration]);
  const shown = motion ? point : { x, y };
  return (
    <g data-testid="animated-vector">
      <line x1="0" y1="0" x2={shown.x} y2={shown.y} stroke="#b34832" strokeWidth="3" />
      <circle cx={shown.x} cy={shown.y} r="4" fill="#1d3548" />
    </g>
  );
}
