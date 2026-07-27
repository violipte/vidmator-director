import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// SUBJECT TITLE CARD — nome grande + datas (subtítulo), tipografia elegante, sem imagem.
// Container do acervo VidMator (ref.: VidRush "chapter / subject title"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const SubjectTitleCard: React.FC<{
  firstTitle?: string;
  firstSubtitle?: string;
  accent?: string;
}> = ({
  firstTitle = "Daniel Burnham",
  firstSubtitle = "1846-1912",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const nameIn = spring({ frame, fps, config: { damping: 18, stiffness: 70 }, durationInFrames: 26 });
  const ruleW = interpolate(frame - 12, [0, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subIn = interpolate(frame - 24, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 18);

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 30%, #12141c 0%, #0a0b0f 70%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
        opacity: outOp,
        overflow: "hidden",
      }}
    >
      {/* grade sutil */}
      <AbsoluteFill
        style={{
          background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
          maskImage: "radial-gradient(ellipse 70% 70% at 50% 50%, black 30%, transparent 90%)",
        }}
      />

      {/* position:relative — sem isso o AbsoluteFill de textura pinta POR CIMA do texto (CSS painting order) */}
      <div style={{ position: "relative", textAlign: "center", padding: "0 8%" }}>
        {/* kicker accent */}
        <div
          style={{
            fontSize: 30,
            fontWeight: 600,
            letterSpacing: 10,
            textTransform: "uppercase",
            color: accent,
            opacity: interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" }),
            marginBottom: 26,
            textShadow: `0 0 ${10 + glow * 12}px ${accent}88`,
          }}
        >
          Subject
        </div>

        {/* nome grande, elegante */}
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 148,
            lineHeight: 0.98,
            color: "#ffffff",
            letterSpacing: -2,
            transform: `translateY(${(1 - nameIn) * 44}px) scale(${0.94 + 0.06 * nameIn})`,
            opacity: nameIn,
            textShadow: "0 12px 44px rgba(0,0,0,0.7)",
          }}
        >
          {firstTitle}
        </div>

        {/* régua accent que cresce */}
        <div
          style={{
            width: interpolate(ruleW, [0, 1], [0, 340]),
            height: 4,
            margin: "34px auto 30px",
            background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
            boxShadow: `0 0 18px ${accent}`,
          }}
        />

        {/* datas / subtítulo */}
        <div
          style={{
            fontSize: 52,
            fontWeight: 300,
            letterSpacing: 8,
            color: "#9aa4b2",
            opacity: subIn,
          }}
        >
          {firstSubtitle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
