import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Icon } from "./_icons";

// ICON LABELS — linha de ícones SVG em cards + labels aparecendo 1 a 1 (pop escalonado).
// Container do acervo VidMator. Niche-agnostic: icons[]/labels[]/accent via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const IconLabels: React.FC<{
  icons?: string[];
  labels?: string[];
  accent?: string;
}> = ({
  icons = ["fuel", "truck", "rocket"],
  labels = ["Fuel", "Transport", "Launch"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        background: "#0a0b0f",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ display: "flex", gap: 90, alignItems: "flex-start" }}>
        {icons.map((icon, i) => {
          const delay = 8 + i * 16;
          const e = spring({ frame: frame - delay, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 18 });
          const s = interpolate(e, [0, 1], [0.3, 1]);
          const op = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const lblOp = interpolate(frame, [delay + 8, delay + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ textAlign: "center", opacity: op, transform: `scale(${s})` }}>
              <div
                style={{
                  width: 200,
                  height: 200,
                  borderRadius: 28,
                  background: "radial-gradient(circle at 50% 38%, #1b1e27 0%, #101218 100%)",
                  border: `1px solid ${accent}44`,
                  boxShadow: `0 20px 50px rgba(0,0,0,0.6), 0 0 34px ${accent}2a`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Icon name={icon} color={accent} size={96} strokeWidth={1.6} />
              </div>
              <div
                style={{
                  marginTop: 26,
                  fontSize: 42,
                  fontWeight: 700,
                  letterSpacing: 2,
                  color: "#fff",
                  textTransform: "uppercase",
                  opacity: lblOp,
                }}
              >
                <span style={{ color: accent }}>—</span> {labels[i] ?? ""}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
