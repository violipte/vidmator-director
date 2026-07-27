import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// DISPLAY TEXT — texto único display animado sobre FUNDO TRANSPARENTE (composita
// sobre imagem/vídeo). Sobe + fade, com barra accent que enche e text-shadow forte
// p/ legibilidade. Container do acervo VidMator (ref.: VidRush "name / label over image").
// Niche-agnostic: text / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const DisplayText: React.FC<{
  text?: string;
  accent?: string;
}> = ({
  text = "Noah Morris",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sp = spring({ frame, fps, config: { damping: 16, stiffness: 95 }, durationInFrames: 22 });
  const y = interpolate(sp, [0, 1], [40, 0]);
  const op = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const barW = interpolate(frame, [12, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div style={{ textAlign: "center", opacity: op, transform: `translateY(${y}px)` }}>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 140,
            color: "#fff",
            letterSpacing: 2,
            textShadow: "0 6px 30px rgba(0,0,0,0.85), 0 2px 8px rgba(0,0,0,0.9)",
          }}
        >
          {text}
        </div>
        <div
          style={{
            width: barW * 200,
            height: 8,
            background: accent,
            borderRadius: 4,
            margin: "26px auto 0",
            boxShadow: `0 0 20px ${accent}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
