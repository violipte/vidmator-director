import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// OBJECT DUAL STAT — recorte (cutout PNG alpha) do objeto ao CENTRO; à esq e dir dois stats
// grandes (número + label) entrando escalonado (slide-in lateral). Container do acervo VidMator.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const ObjectDualStat: React.FC<{
  objectImage?: string;
  leftBigNumber?: string;
  leftLabel?: string;
  rightBigNumber?: string;
  rightLabel?: string;
  accent?: string;
}> = ({
  objectImage = "test/people/pessoa_0.png",
  leftBigNumber = "60",
  leftLabel = "TONS",
  rightBigNumber = "9.4",
  rightLabel = "METERS",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const objE = spring({ frame, fps, config: { damping: 18, stiffness: 80 }, durationInFrames: 24 });
  const objScale = interpolate(objE, [0, 1], [0.85, 1]);
  const objOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  const leftE = spring({ frame: frame - 12, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 20 });
  const rightE = spring({ frame: frame - 22, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 20 });

  const stat = (big: string, label: string, e: number, side: "left" | "right") => (
    <div
      style={{
        textAlign: "center",
        opacity: e,
        transform: `translateX(${interpolate(e, [0, 1], [side === "left" ? -70 : 70, 0])}px)`,
      }}
    >
      <div
        style={{
          fontFamily: DISPLAY,
          fontSize: 170,
          fontWeight: 900,
          color: "#fff",
          lineHeight: 1,
          textShadow: `0 0 30px ${accent}66`,
        }}
      >
        {big}
      </div>
      <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: 5, color: accent, textTransform: "uppercase", marginTop: 10 }}>
        {label}
      </div>
    </div>
  );

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 50%, #12151c 0%, #0a0b0f 70%)",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", gap: 40 }}>
        <div style={{ flex: "0 0 27%", display: "flex", justifyContent: "flex-end" }}>{stat(leftBigNumber, leftLabel, leftE, "left")}</div>
        <Img
          src={staticFile(objectImage)}
          style={{
            height: 780,
            maxWidth: "34%",
            objectFit: "contain",
            opacity: objOp,
            transform: `scale(${objScale})`,
            filter: "drop-shadow(0 24px 50px rgba(0,0,0,0.7))",
          }}
        />
        <div style={{ flex: "0 0 27%", display: "flex", justifyContent: "flex-start" }}>{stat(rightBigNumber, rightLabel, rightE, "right")}</div>
      </div>
    </AbsoluteFill>
  );
};
