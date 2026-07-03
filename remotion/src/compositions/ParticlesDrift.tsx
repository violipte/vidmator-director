import { AbsoluteFill, useCurrentFrame, useVideoConfig, random } from "remotion";

const PARTICLE_COUNT = 80;

export const ParticlesDrift: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0d0820 0%, #050510 100%)" }}>
      {Array.from({ length: PARTICLE_COUNT }).map((_, i) => {
        const seedX = random(`x${i}`);
        const seedSpeed = random(`speed${i}`) * 0.5 + 0.3;
        const seedSize = random(`size${i}`) * 4 + 1.5;
        const seedOpacity = random(`op${i}`) * 0.7 + 0.3;
        const seedDrift = random(`drift${i}`) * 30 - 15;
        const x = seedX * width + Math.sin(t * 0.5 + i) * seedDrift;
        const yProgress = ((t * seedSpeed * 100) + i * 73) % (height + 100);
        const y = height - yProgress;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: seedSize,
              height: seedSize,
              borderRadius: "50%",
              background: "#facc15",
              opacity: seedOpacity,
              boxShadow: `0 0 ${seedSize * 3}px rgba(250, 204, 21, 0.6)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
