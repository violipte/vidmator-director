import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// SINGLE SENTENCE TEXT SLIDE — uma frase deslizando da direita (fade) + barra accent
// que enche embaixo como destaque. Alinhada à esquerda, display grande.
// Container do acervo VidMator (ref.: VidRush "single sentence slide").
// Niche-agnostic: sentence / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

export const SingleSentenceTextSlide: React.FC<{
  sentence?: string;
  accent?: string;
}> = ({
  sentence = "A single powerful sentence.",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sp = spring({ frame, fps, config: { damping: 18, stiffness: 85 }, durationInFrames: 26 });
  const x = interpolate(sp, [0, 1], [120, 0]);
  const op = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const barW = interpolate(frame, [14, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const barOp = interpolate(frame, [14, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 30% 50%, #14161c 0%, #0a0b0f 70%)",
        justifyContent: "center",
        alignItems: "flex-start",
        fontFamily: DISPLAY,
        padding: "0 180px",
      }}
    >
      <div style={{ overflow: "hidden" }}>
        <div
          style={{
            fontSize: 104,
            lineHeight: 1.2,
            color: "#fff",
            maxWidth: 1500,
            opacity: op,
            transform: `translateX(${x}px)`,
            textShadow: "0 6px 30px rgba(0,0,0,0.6)",
          }}
        >
          {sentence}
        </div>
      </div>
      <div
        style={{
          width: barW * 340,
          height: 10,
          background: accent,
          borderRadius: 5,
          marginTop: 46,
          opacity: barOp,
          boxShadow: `0 0 24px ${accent}`,
        }}
      />
    </AbsoluteFill>
  );
};
