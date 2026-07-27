import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// TWO IMAGE COMPARISON — título no topo + 2 fotos emolduradas entrando (esq/dir) com pop.
// Container do acervo VidMator (ref.: comparativo lado-a-lado do VidRush).
// Niche-agnostic: titleText/leftImage/rightImage/accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const BG = "#0a0b0f";

export const TwoImageComparison: React.FC<{
  titleText?: string;
  leftImage?: string;
  rightImage?: string;
  accent?: string;
}> = ({
  titleText = "Two Image Comparison",
  leftImage = "test/clips/scene_10.jpg",
  rightImage = "test/clips/scene_100.jpg",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleY = interpolate(frame, [0, 14], [-40, 0], { extrapolateRight: "clamp" });

  const sl = spring({ frame: frame - 8, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 24 });
  const sr = spring({ frame: frame - 16, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 24 });
  const lx = interpolate(sl, [0, 1], [-140, 0]);
  const rx = interpolate(sr, [0, 1], [140, 0]);

  const frameStyle = (extra: object): React.CSSProperties => ({
    width: "42%",
    height: "62%",
    borderRadius: 16,
    overflow: "hidden",
    border: "4px solid rgba(255,255,255,0.92)",
    boxShadow: `0 24px 70px rgba(0,0,0,0.7), 0 0 0 6px ${accent}22`,
    ...extra,
  });

  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 100% at 50% 40%, #14161c 0%, ${BG} 70%)`, alignItems: "center" }}>
      <div
        style={{
          marginTop: 66,
          fontFamily: DISPLAY,
          fontSize: 72,
          color: "#fff",
          letterSpacing: 1,
          textTransform: "uppercase",
          textAlign: "center",
          opacity: titleOp,
          transform: `translateY(${titleY}px)`,
          textShadow: `0 0 24px ${accent}66`,
        }}
      >
        {titleText}
      </div>
      <div
        style={{
          width: 220,
          height: 5,
          marginTop: 18,
          borderRadius: 3,
          background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
          boxShadow: `0 0 18px ${accent}`,
          opacity: titleOp,
        }}
      />
      <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 60, padding: "20px 90px 70px" }}>
        <div style={frameStyle({ opacity: sl, transform: `translateX(${lx}px) rotate(-2deg)` })}>
          <Img src={staticFile(leftImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 56,
            color: accent,
            opacity: interpolate(frame, [22, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            textShadow: `0 0 24px ${accent}`,
          }}
        >
          VS
        </div>
        <div style={frameStyle({ opacity: sr, transform: `translateX(${rx}px) rotate(2deg)` })}>
          <Img src={staticFile(rightImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
