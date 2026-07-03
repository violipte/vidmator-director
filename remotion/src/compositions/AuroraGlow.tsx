import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

export const AuroraGlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const rotate1 = (t * 8) % 360;
  const rotate2 = (-t * 5 + 60) % 360;
  return (
    <AbsoluteFill style={{ background: "#040410", overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: "conic-gradient(from 0deg at 30% 40%, rgba(139, 92, 246, 0.55), rgba(6, 182, 212, 0.45), rgba(16, 185, 129, 0.45), rgba(139, 92, 246, 0.55))",
          transform: `rotate(${rotate1}deg) scale(1.5)`,
          filter: "blur(80px)",
          opacity: 0.7,
        }}
      />
      <AbsoluteFill
        style={{
          background: "conic-gradient(from 180deg at 70% 60%, rgba(250, 204, 21, 0.3), transparent, rgba(139, 92, 246, 0.4), transparent)",
          transform: `rotate(${rotate2}deg) scale(1.4)`,
          filter: "blur(100px)",
          opacity: 0.6,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(circle at center, transparent 30%, rgba(4, 4, 16, 0.8) 100%)" }} />
    </AbsoluteFill>
  );
};
