import { AbsoluteFill, useCurrentFrame, useVideoConfig, random } from "remotion";

const STAR_COUNT = 120;

export const StarsDrifting: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0a0820 0%, #02020a 100%)" }}>
      {Array.from({ length: STAR_COUNT }).map((_, i) => {
        const baseX = random(`sx${i}`) * width;
        const baseY = random(`sy${i}`) * height;
        const driftSpeed = random(`drift${i}`) * 10 + 5;
        const x = (baseX + t * driftSpeed) % width;
        const y = baseY;
        const size = random(`size${i}`) * 2 + 0.8;
        const twinkle = 0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i * 0.5));
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              background: "#ffffff",
              opacity: twinkle,
              boxShadow: `0 0 ${size * 4}px rgba(255, 255, 255, 0.7)`,
            }}
          />
        );
      })}
      {/* Linhas conectando algumas estrelas */}
      <svg width={width} height={height} style={{ position: "absolute", inset: 0, opacity: 0.15 }}>
        {Array.from({ length: 8 }).map((_, i) => {
          const x1 = random(`lx1-${i}`) * width;
          const y1 = random(`ly1-${i}`) * height;
          const x2 = x1 + (random(`lx2-${i}`) * 300 - 150);
          const y2 = y1 + (random(`ly2-${i}`) * 200 - 100);
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#ffffff" strokeWidth={0.5} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};
