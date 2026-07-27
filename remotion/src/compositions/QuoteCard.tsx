import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// QUOTE CARD — aspa gigante accent (pop) + citação em itálico serif (fade/sobe) +
// atribuição (name em accent / title dim) deslizando. Fundo escuro cinematográfico.
// Container do acervo VidMator (ref.: VidRush "quote card").
// Niche-agnostic: quoteText / name / title / accent via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";
const SERIF = "'Georgia', 'Times New Roman', serif";

export const QuoteCard: React.FC<{
  quoteText?: string;
  name?: string;
  title?: string;
  accent?: string;
}> = ({
  quoteText = "Only three people have ever understood it.",
  name = "Lord Palmerston",
  title = "British Prime Minister",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const markSp = spring({ frame, fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 24 });
  const markScale = interpolate(markSp, [0, 1], [0.3, 1]);
  const markOp = interpolate(frame, [0, 14], [0, 0.9], { extrapolateRight: "clamp" });

  const quoteOp = interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const quoteY = interpolate(frame, [16, 34], [26, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const attrOp = interpolate(frame, [40, 56], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const attrX = interpolate(frame, [40, 56], [-30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 30%, #14161c 0%, #0a0b0f 72%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ width: 1360, textAlign: "center" }}>
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 320,
            lineHeight: 0.7,
            height: 150,
            color: accent,
            opacity: markOp,
            transform: `scale(${markScale})`,
            textShadow: `0 0 50px ${accent}66`,
          }}
        >
          &ldquo;
        </div>
        <div
          style={{
            fontFamily: SERIF,
            fontSize: 76,
            fontStyle: "italic",
            lineHeight: 1.4,
            color: "#fff",
            opacity: quoteOp,
            transform: `translateY(${quoteY}px)`,
            textShadow: "0 4px 24px rgba(0,0,0,0.5)",
          }}
        >
          {quoteText}
        </div>
        <div style={{ marginTop: 56, opacity: attrOp, transform: `translateX(${attrX}px)` }}>
          <div style={{ width: 90, height: 4, background: accent, margin: "0 auto 26px", borderRadius: 2 }} />
          <div style={{ fontSize: 46, fontWeight: 700, color: accent, letterSpacing: 1 }}>{name}</div>
          <div style={{ fontSize: 32, color: "#9aa4b2", marginTop: 10, letterSpacing: 2, textTransform: "uppercase" }}>
            {title}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
