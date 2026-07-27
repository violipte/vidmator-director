import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

// DUAL IMPACT SENTENCE — fundo gradiente escuro; 2 frases de impacto dão fade-in em
// sequência (grandes, centralizadas, display). A 1ª esmaece ao entrar a 2ª (accent),
// separadas por divisor accent. Container do acervo VidMator (ref.: VidRush "two impact lines").
// Niche-agnostic: firstSentence / secondSentence / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

export const DualImpactSentence: React.FC<{
  firstSentence?: string;
  secondSentence?: string;
  accent?: string;
}> = ({
  firstSentence = "Everyone knew the system was broken.",
  secondSentence = "Nobody had the courage to fix it.",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();

  const firstOp = interpolate(frame, [6, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const firstY = interpolate(frame, [6, 28], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const secondOp = interpolate(frame, [44, 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const secondY = interpolate(frame, [44, 66], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dim1 = interpolate(frame, [44, 66], [1, 0.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(160deg, #14161c 0%, #0a0b0f 55%, #05060a 100%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: DISPLAY,
        padding: "0 200px",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: 92,
            lineHeight: 1.25,
            color: "#fff",
            opacity: firstOp * dim1,
            transform: `translateY(${firstY}px)`,
            textShadow: "0 6px 30px rgba(0,0,0,0.6)",
          }}
        >
          {firstSentence}
        </div>
        <div
          style={{
            width: 120,
            height: 5,
            background: accent,
            borderRadius: 3,
            margin: "50px auto",
            opacity: secondOp,
            boxShadow: `0 0 20px ${accent}`,
          }}
        />
        <div
          style={{
            fontSize: 92,
            lineHeight: 1.25,
            color: accent,
            opacity: secondOp,
            transform: `translateY(${secondY}px)`,
            textShadow: `0 0 40px ${accent}44`,
          }}
        >
          {secondSentence}
        </div>
      </div>
    </AbsoluteFill>
  );
};
