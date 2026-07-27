import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// VINTAGE ANGLED — foto ANTIGA (P&B/sépia) com zoom + LEVE ROTAÇÃO (~15°) + vinheta e grão.
// Container do acervo VidMator (ref.: formato Harley/VidRush, foto histórica angulada).
// dir = "out" (zoom-out) | "in" (zoom-in). src = staticFile rel de uma imagem real do tema.
export const VintageAngled: React.FC<{ src?: string; dir?: "in" | "out" }> = ({
  src = "test/clips/scene_0.jpg",
  dir = "out",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: "clamp" });
  const scale = dir === "out" ? interpolate(t, [0, 1], [1.30, 1.10]) : interpolate(t, [0, 1], [1.10, 1.30]);
  const rot = interpolate(t, [0, 1], [-19, -4]);                       // angulado, girando ~15°
  const op = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ opacity: op }}>
        <Img
          src={staticFile(src)}
          style={{
            position: "absolute",
            width: "116%",
            height: "116%",
            left: "-8%",
            top: "-8%",
            objectFit: "cover",
            transform: `scale(${scale}) rotate(${rot}deg)`,
            filter: "grayscale(1) contrast(1.08) brightness(0.9) sepia(0.18)",
          }}
        />
      </AbsoluteFill>
      {/* vinheta de época */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 82% 82% at 50% 50%, transparent 44%, rgba(0,0,0,0.74) 100%)" }} />
      {/* grão/scanline sutil */}
      <AbsoluteFill
        style={{
          background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 4px)",
          opacity: 0.4,
          mixBlendMode: "overlay",
        }}
      />
    </AbsoluteFill>
  );
};
