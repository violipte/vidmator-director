import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// ONE WORD CALLOUT — uma palavra GIGANTE que SLAM-in (scale down + de-blur + glow) no centro.
// Container do acervo VidMator. Niche-agnostic: word/accent via props; fonte auto-ajusta ao comprimento.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

export const OneWordCallout: React.FC<{ word?: string; accent?: string }> = ({
  word = "UNKILLABLE",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = spring({ frame, fps, config: { damping: 12, stiffness: 140, mass: 0.8 }, durationInFrames: 18 });
  const scale = interpolate(e, [0, 1], [2.6, 1]);                       // slam: escala grande -> 1
  const op = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const blur = interpolate(frame, [0, 10], [22, 0], { extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 12);
  const size = Math.min(300, 1632 / (Math.max(word.length, 4) * 0.62)); // cabe em ~85% da largura

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: DISPLAY,
          fontSize: size,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 2,
          textAlign: "center",
          transform: `scale(${scale})`,
          opacity: op,
          filter: `blur(${blur}px)`,
          textShadow: `0 0 ${30 + glow * 34}px ${accent}, 0 0 ${70 + glow * 60}px ${accent}88`,
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        {word}
      </div>
    </AbsoluteFill>
  );
};
