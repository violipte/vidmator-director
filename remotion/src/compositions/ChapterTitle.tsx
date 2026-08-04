import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// CHAPTER TITLE — abertura de capítulo cinematográfica: label "CHAPTER", número
// gigante accent (zoom-out + glow), réguas que expandem, título display + subtítulo.
// Container do acervo VidMator (ref.: VidRush "chapter title card").
// Niche-agnostic: title / chapterNumber / subtitle / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const ChapterTitle: React.FC<{
  title?: string;
  chapterNumber?: number;
  subtitle?: string;
  accent?: string;
  /* 02/08: o rótulo era "Chapter" FIXO. Num "Top 5" o narrador diz "Number Five" e
     a tela contradizia ele com "CHAPTER 01". O rótulo vem do roteiro. */
  label?: string;
}> = ({
  title = "THE ORIGIN",
  chapterNumber = 1,
  label = "Chapter",
  subtitle = "The greatest empire",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const numSp = spring({ frame, fps, config: { damping: 16, stiffness: 80 }, durationInFrames: 26 });
  const numScale = interpolate(numSp, [0, 1], [1.5, 1]);
  const numOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  const lineW = interpolate(frame, [18, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleOp = interpolate(frame, [30, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [30, 48], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subOp = interpolate(frame, [46, 62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const glow = 0.5 + 0.5 * Math.sin(frame / 15);
  const num = String(chapterNumber).padStart(2, "0");

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(130% 110% at 50% 42%, #16130c 0%, #0a0b0f 68%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: 34,
            letterSpacing: 16,
            color: "#9aa4b2",
            textTransform: "uppercase",
            opacity: numOp,
            marginBottom: 6,
            paddingLeft: 16,
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 300,
            lineHeight: 1,
            color: accent,
            opacity: numOp,
            transform: `scale(${numScale})`,
            textShadow: `0 0 ${30 + glow * 40}px ${accent}88`,
          }}
        >
          {num}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 30, margin: "34px 0 30px" }}>
          <div style={{ width: lineW * 220, height: 2, background: `linear-gradient(90deg, transparent, ${accent})` }} />
          <div
            style={{
              width: 8,
              height: 8,
              background: accent,
              borderRadius: "50%",
              transform: `scale(${lineW})`,
              boxShadow: `0 0 12px ${accent}`,
            }}
          />
          <div style={{ width: lineW * 220, height: 2, background: `linear-gradient(90deg, ${accent}, transparent)` }} />
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 108,
            color: "#fff",
            letterSpacing: 6,
            opacity: titleOp,
            transform: `translateY(${titleY}px)`,
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: 44,
            fontWeight: 300,
            color: "#9aa4b2",
            marginTop: 26,
            letterSpacing: 3,
            fontStyle: "italic",
            opacity: subOp,
          }}
        >
          {subtitle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
