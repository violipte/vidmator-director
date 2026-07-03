import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_A_COLOR, TEXT_PRIMARY } from "./_shared";

export const LightLeak: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const t = frame / fps;
  // Pulso de luz entrando pelo canto superior direito
  const intensity = interpolate(frame, [0, durationInFrames / 2, durationInFrames], [0.2, 1, 0.3], { extrapolateRight: "clamp" });
  const shift = Math.sin(t * 0.8) * 15;
  return (
    <AbsoluteFill style={{ background: SCENE_A_COLOR }}>
      {/* Conteúdo simulando vídeo embaixo */}
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 80, fontWeight: 700, fontFamily: "serif", opacity: 0.85 }}>
          Your Video Here
        </div>
      </AbsoluteFill>
      {/* Vazamento de luz quente */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${75 + shift}% ${20}%, rgba(255, 180, 90, ${0.5 * intensity}) 0%, rgba(255, 120, 60, ${0.3 * intensity}) 25%, transparent 60%)`,
          mixBlendMode: "screen",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at ${85 - shift}% ${10}%, rgba(255, 240, 200, ${0.4 * intensity}) 0%, transparent 40%)`,
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};
