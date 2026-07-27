import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// TEXT REVEAL — 3 textos revelam em sequência: mainText grande (zoom-in) →
// secondaryText desliza → finalLabel em pill accent com glow (pop).
// Container do acervo VidMator (ref.: VidRush "sequential text reveal").
// Niche-agnostic: mainText / secondaryText / finalLabel / accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const TextReveal: React.FC<{
  mainText?: string;
  secondaryText?: string;
  finalLabel?: string;
  accent?: string;
}> = ({
  mainText = "HELLO",
  secondaryText = "World of Animation",
  finalLabel = "Complete",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const mainSp = spring({ frame, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 22 });
  const mainScale = interpolate(mainSp, [0, 1], [1.4, 1]);
  const mainOp = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });

  const secSp = spring({ frame: frame - 26, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 20 });
  const secOp = interpolate(frame, [26, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const secY = interpolate(secSp, [0, 1], [30, 0]);

  const finSp = spring({ frame: frame - 54, fps, config: { damping: 12, stiffness: 120 }, durationInFrames: 18 });
  const finScale = interpolate(finSp, [0, 1], [0.6, 1]);
  const finOp = interpolate(frame, [54, 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 13);

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 40%, #14161c 0%, #0a0b0f 70%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 240,
            color: "#fff",
            lineHeight: 1,
            opacity: mainOp,
            transform: `scale(${mainScale})`,
            letterSpacing: 2,
            textShadow: "0 8px 40px rgba(0,0,0,0.6)",
          }}
        >
          {mainText}
        </div>
        <div
          style={{
            fontSize: 66,
            fontWeight: 300,
            color: "#9aa4b2",
            marginTop: 24,
            opacity: secOp,
            transform: `translateY(${secY}px)`,
            letterSpacing: 6,
          }}
        >
          {secondaryText}
        </div>
        <div style={{ display: "inline-block", marginTop: 48, opacity: finOp, transform: `scale(${finScale})` }}>
          <span
            style={{
              fontSize: 42,
              fontWeight: 800,
              letterSpacing: 4,
              textTransform: "uppercase",
              color: "#0a0b0f",
              background: accent,
              padding: "14px 40px",
              borderRadius: 10,
              boxShadow: `0 0 ${24 + glow * 30}px ${accent}`,
            }}
          >
            {finalLabel}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
