import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

export const LightRays: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  // 6 raios saindo do topo central, pulsando
  const rays = [-30, -18, -6, 6, 18, 30];
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at top, #1a1a2e 0%, #050510 100%)" }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="rayGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(250, 204, 21, 0.55)" />
            <stop offset="100%" stopColor="rgba(250, 204, 21, 0)" />
          </linearGradient>
        </defs>
        {rays.map((angle, i) => {
          const breath = 0.4 + 0.3 * Math.sin(t * 1.2 + i * 0.3);
          return (
            <polygon
              key={i}
              points={`${width / 2 - 80},0 ${width / 2 + 80},0 ${width / 2 + 600},${height * 1.3} ${width / 2 - 600},${height * 1.3}`}
              fill="url(#rayGrad)"
              opacity={breath}
              transform={`rotate(${angle} ${width / 2} 0)`}
            />
          );
        })}
      </svg>
      <AbsoluteFill style={{ background: "radial-gradient(circle at center top, rgba(250, 204, 21, 0.15) 0%, transparent 50%)", opacity: 0.6 + 0.3 * Math.sin(t * 1.5) }} />
    </AbsoluteFill>
  );
};
