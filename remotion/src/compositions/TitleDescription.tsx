import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// TITLE DESCRIPTION — card escuro: título display grande + barra accent que enche
// + descrição secundária. Entrada: card pop, título sobe, barra cresce, texto fade.
// Container do acervo VidMator (ref.: VidRush "title + description card").
// Niche-agnostic: title / description / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const TitleDescription: React.FC<{
  title?: string;
  description?: string;
  accent?: string;
}> = ({
  title = "Frogs",
  description = "The two frogs are trapped in a bucket of cream.",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardIn = spring({ frame, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 24 });
  const cardScale = interpolate(cardIn, [0, 1], [0.92, 1]);

  const titleSp = spring({ frame: frame - 6, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 22 });
  const titleY = interpolate(titleSp, [0, 1], [40, 0]);
  const titleOp = interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const barW = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const descOp = interpolate(frame, [34, 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const descY = interpolate(frame, [34, 52], [24, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          width: 1280,
          background: "#14161c",
          borderRadius: 16,
          padding: "110px 120px",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          transform: `scale(${cardScale})`,
          opacity: cardIn,
        }}
      >
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 150,
            color: "#fff",
            lineHeight: 1,
            opacity: titleOp,
            transform: `translateY(${titleY}px)`,
            letterSpacing: 1,
          }}
        >
          {title}
        </div>
        <div
          style={{
            width: barW * 260,
            height: 8,
            background: accent,
            borderRadius: 4,
            margin: "36px 0 40px",
            boxShadow: `0 0 18px ${accent}`,
          }}
        />
        <div
          style={{
            fontSize: 56,
            lineHeight: 1.5,
            color: "#9aa4b2",
            fontWeight: 400,
            opacity: descOp,
            transform: `translateY(${descY}px)`,
          }}
        >
          {description}
        </div>
      </div>
    </AbsoluteFill>
  );
};
