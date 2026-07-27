import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// STAT REVEAL — dado grande em fundo âmbar/preto, fonte typewriter, entrada ZOOM-OUT + glow.
// Container do acervo VidMator (ref.: formato Harley/VidRush "76% MORE HORSEPOWER").
// Niche-agnostic: value/label/sub/accent via props. O Director sincroniza a entrada com a fala.
const MONO = "'American Typewriter', 'Courier New', monospace";

export const StatReveal: React.FC<{
  value?: string;
  label?: string;
  sub?: string;
  accent?: string;
}> = ({
  value = "76%",
  label = "MORE HORSEPOWER",
  sub = "1985 Evolution vs. 2025 Milwaukee-Eight 117",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = spring({ frame, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 22 });
  const scale = interpolate(e, [0, 1], [1.32, 1]);                    // zoom-out na entrada
  const op = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const lblOp = interpolate(frame, [11, 25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subOp = interpolate(frame, [22, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 14);                      // respiração leve do glow

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 92% at 50% 80%, ${accent}22 0%, #150d05 42%, #080604 100%)`,
        justifyContent: "center",
        alignItems: "center",
        fontFamily: MONO,
      }}
    >
      <div style={{ textAlign: "center", transform: `scale(${scale})`, opacity: op }}>
        <div
          style={{
            fontFamily: "'Impact', 'Arial Black', sans-serif",
            fontSize: 224,
            fontWeight: 900,
            color: "#fff",
            lineHeight: 1,
            textShadow: `0 0 ${26 + glow * 26}px ${accent}, 0 0 ${58 + glow * 44}px ${accent}88`,
          }}
        >
          {value}
        </div>
        <div
          style={{
            width: 210,
            height: 3,
            margin: "20px auto 26px",
            background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
            boxShadow: `0 0 18px ${accent}`,
            opacity: lblOp,
          }}
        />
        <div style={{ fontSize: 46, fontWeight: 700, letterSpacing: 3, color: accent, textTransform: "uppercase", opacity: lblOp }}>
          {label}
        </div>
        <div style={{ fontSize: 29, color: "#9a8f82", marginTop: 16, opacity: subOp, fontFamily: "'Segoe UI', sans-serif" }}>
          {sub}
        </div>
      </div>
    </AbsoluteFill>
  );
};
