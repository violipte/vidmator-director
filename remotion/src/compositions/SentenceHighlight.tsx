import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// SENTENCE HIGHLIGHT — card claro, parágrafos entram e frases-chave recebem
// marca-texto (highlighter) accent que varre da esquerda p/ direita, sequencialmente.
// Container do acervo VidMator (ref.: VidRush "highlight text in paragraphs").
// Niche-agnostic: paragraphs[] + highlights[] (1 frase por parágrafo) + accent.
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const SentenceHighlight: React.FC<{
  paragraphs?: string[];
  highlights?: string[];
  accent?: string;
}> = ({
  paragraphs = [
    "This animation highlights specific text within paragraphs.",
    "The animation moves sequentially through all paragraphs.",
    "For best results, keep highlight phrases short.",
  ],
  highlights = ["specific text", "sequentially", "short"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardIn = spring({ frame, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 24 });
  const cardScale = interpolate(cardIn, [0, 1], [0.94, 1]);

  const P_START = 8;
  const P_STAGGER = 10;
  const H_START = P_START + paragraphs.length * P_STAGGER + 12;
  const H_STAGGER = 26;

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          width: 1360,
          background: "#f5f3ec",
          borderRadius: 24,
          padding: "96px 110px",
          boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
          border: "1px solid rgba(0,0,0,0.06)",
          transform: `scale(${cardScale})`,
          opacity: cardIn,
        }}
      >
        {paragraphs.map((para, i) => {
          const pIn = P_START + i * P_STAGGER;
          const pOp = interpolate(frame, [pIn, pIn + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const pY = interpolate(frame, [pIn, pIn + 16], [18, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          const phrase = highlights[i] ?? "";
          const idx = phrase ? para.indexOf(phrase) : -1;
          const hStart = H_START + i * H_STAGGER;
          const hp = interpolate(frame, [hStart, hStart + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

          const before = idx >= 0 ? para.slice(0, idx) : para;
          const match = idx >= 0 ? para.slice(idx, idx + phrase.length) : "";
          const after = idx >= 0 ? para.slice(idx + phrase.length) : "";

          return (
            <p
              key={i}
              style={{
                fontSize: 52,
                lineHeight: 1.5,
                fontWeight: 600,
                color: "#191b21",
                margin: i === 0 ? 0 : "40px 0 0",
                opacity: pOp,
                transform: `translateY(${pY}px)`,
              }}
            >
              {before}
              {match && (
                <span
                  style={{
                    backgroundImage: `linear-gradient(to top, ${accent}cc 0%, ${accent}cc 58%, transparent 58%)`,
                    backgroundRepeat: "no-repeat",
                    backgroundSize: `${hp * 100}% 100%`,
                    borderRadius: 3,
                    padding: "0 3px",
                    boxDecorationBreak: "clone",
                    WebkitBoxDecorationBreak: "clone",
                  }}
                >
                  {match}
                </span>
              )}
              {after}
            </p>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
