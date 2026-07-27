import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// OBJECT TITLE — objeto/recorte em destaque (spotlight) + título grande embaixo.
// Container do acervo VidMator (ref.: VidRush "object reveal"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const ObjectTitle: React.FC<{
  objectImage?: string;
  title?: string;
  accent?: string;
}> = ({
  objectImage = "test/people/pessoa_3.png",
  title = "Navigation System",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const objE = spring({ frame, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 24 });
  const objScale = interpolate(objE, [0, 1], [1.18, 1]);
  const objOp = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const titleIn = spring({ frame: frame - 16, fps, config: { damping: 16 }, durationInFrames: 22 });
  const barW = interpolate(frame - 20, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 15);

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", opacity: outOp, overflow: "hidden", fontFamily: SANS }}>
      {/* spotlight cônico no objeto */}
      <AbsoluteFill style={{ background: `radial-gradient(48% 46% at 50% 40%, ${accent}22 0%, transparent 60%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 95% 95% at 50% 42%, transparent 40%, rgba(0,0,0,0.72) 100%)" }} />

      {/* objeto recortado, centralizado em cima */}
      <div
        style={{
          position: "absolute",
          top: "6%",
          left: 0,
          right: 0,
          height: "62%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: objOp,
          transform: `scale(${objScale})`,
        }}
      >
        <Img
          src={staticFile(objectImage)}
          style={{
            maxHeight: "100%",
            maxWidth: "70%",
            objectFit: "contain",
            filter: `drop-shadow(0 20px 50px rgba(0,0,0,0.75)) drop-shadow(0 0 ${20 + glow * 20}px ${accent}55)`,
          }}
        />
      </div>

      {/* título embaixo */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: "9%",
          textAlign: "center",
          transform: `translateY(${(1 - titleIn) * 50}px)`,
          opacity: titleIn,
        }}
      >
        <div
          style={{
            width: interpolate(barW, [0, 1], [0, 260]),
            height: 4,
            margin: "0 auto 22px",
            background: accent,
            boxShadow: `0 0 16px ${accent}`,
          }}
        />
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 96,
            lineHeight: 1,
            color: "#ffffff",
            letterSpacing: -1,
            textShadow: "0 8px 30px rgba(0,0,0,0.7)",
          }}
        >
          {title}
        </div>
      </div>
    </AbsoluteFill>
  );
};
