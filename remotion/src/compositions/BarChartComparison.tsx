import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// BAR CHART COMPARISON — card CLARO; 2 barras verticais (esq vermelha, dir azul) enchendo;
// % no topo de cada; labels embaixo; título no topo do card.
// Container do acervo VidMator (ref.: VidRush "Operational Uptime"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";
const RED = "#ef4444";
const BLUE = "#3b82f6";

export const BarChartComparison: React.FC<{
  chartTitle?: string;
  leftLabel?: string;
  leftValue?: number;
  rightLabel?: string;
  rightValue?: number;
  accent?: string;
}> = ({
  chartTitle = "Operational Uptime",
  leftLabel = "Toyota Hilux",
  leftValue = 92,
  rightLabel = "Other platforms",
  rightValue = 84,
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 24 });

  const grow = (delay: number) =>
    interpolate(frame, [14 + delay, 70 + delay], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });

  const bars = [
    { label: leftLabel, value: Math.max(0, Math.min(100, leftValue)), color: RED, g: grow(0) },
    { label: rightLabel, value: Math.max(0, Math.min(100, rightValue)), color: BLUE, g: grow(8) },
  ];

  const trackH = 470;

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          width: 1160,
          height: 860,
          background: "#f6f7f9",
          borderRadius: 28,
          boxShadow: "0 30px 90px rgba(0,0,0,0.6)",
          border: `1px solid rgba(0,0,0,0.06)`,
          padding: "56px 80px", overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          transform: `scale(${interpolate(enter, [0, 1], [0.94, 1])})`,
          opacity: enter,
        }}
      >
        <div style={{ fontFamily: DISPLAY, fontSize: 62, color: "#111318", textAlign: "center", marginBottom: 8 }}>
          {chartTitle}
        </div>
        <div style={{ width: 90, height: 5, background: accent, borderRadius: 4, margin: "0 auto 40px", boxShadow: `0 0 14px ${accent}aa` }} />

        <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "flex-end", gap: 160 }}>
          {bars.map((b, i) => {
            const h = trackH * (b.value / 100) * b.g;
            return (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 230 }}>
                <div style={{ fontFamily: DISPLAY, fontSize: 68, color: b.color, marginBottom: 14 }}>
                  {Math.round(b.value * b.g)}%
                </div>
                <div style={{ position: "relative", width: 190, height: trackH, background: "#e5e8ec", borderRadius: 16, overflow: "hidden", boxShadow: "inset 0 2px 8px rgba(0,0,0,0.08)" }}>
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      right: 0,
                      bottom: 0,
                      height: h,
                      background: `linear-gradient(180deg, ${b.color} 0%, ${b.color}cc 100%)`,
                      borderRadius: 16,
                      boxShadow: `0 0 24px ${b.color}66`,
                    }}
                  />
                </div>
                <div style={{ marginTop: 22, fontSize: 34, fontWeight: 700, color: "#2a2e36", textAlign: "center", maxWidth: 260 }}>
                  {b.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
