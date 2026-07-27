import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// PIE CHART — donut animando (fatias crescem em ângulo, wipe horário). A fatia destacada
// (highlightedValue) sai levemente + label; legenda à direita. Fundo grid escuro.
// Container do acervo VidMator. Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";
const PALETTE = ["#38bdf8", "#a78bfa", "#34d399", "#f472b6", "#fb923c", "#facc15", "#60a5fa"];

const polar = (cx: number, cy: number, r: number, deg: number) => {
  const rad = (deg * Math.PI) / 180;
  return { x: cx + r * Math.sin(rad), y: cy - r * Math.cos(rad) };
};
const wedge = (cx: number, cy: number, r: number, a0: number, a1: number) => {
  const large = a1 - a0 > 180 ? 1 : 0;
  const p0 = polar(cx, cy, r, a0);
  const p1 = polar(cx, cy, r, a1);
  return `M ${cx} ${cy} L ${p0.x} ${p0.y} A ${r} ${r} 0 ${large} 1 ${p1.x} ${p1.y} Z`;
};

export const PieChart: React.FC<{
  title?: string;
  slices?: number[];
  highlightedValue?: number;
  highlightLabel?: string;
  accent?: string;
}> = ({
  title = "Pie Chart Title",
  slices = [30, 20, 10, 5, 5],
  highlightedValue = 40,
  highlightLabel = "Highlighted Category",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const data = [
    { value: highlightedValue, label: highlightLabel, color: accent, hi: true },
    ...slices.map((v, i) => ({ value: v, label: `Category ${i + 1}`, color: PALETTE[i % PALETTE.length], hi: false })),
  ];
  const total = data.reduce((s, d) => s + d.value, 0) || 1;

  const sweep = interpolate(frame, [10, 74], [0, 360], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const enter = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 26 });
  const pop = interpolate(frame, [56, 84], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  const cx = 260;
  const cy = 300;
  const r = 230;
  let cursor = 0;
  const arcs = data.map((d) => {
    const a0 = (cursor / total) * 360;
    cursor += d.value;
    const a1 = (cursor / total) * 360;
    const mid = (a0 + a1) / 2;
    const off = d.hi ? pop * 34 : 0;
    const o = polar(0, 0, off, mid);
    const drawnEnd = Math.max(a0, Math.min(a1, sweep));
    return { d, a0, a1, drawnEnd, dx: o.x, dy: o.y };
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0b0f",
        backgroundImage:
          "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        fontFamily: SANS,
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          fontFamily: DISPLAY,
          fontSize: 64,
          color: "#ffffff",
          opacity: titleOp,
          transform: `translateY(${interpolate(titleOp, [0, 1], [-20, 0])}px)`,
          marginBottom: 40,
        }}
      >
        {title}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 90, transform: `scale(${interpolate(enter, [0, 1], [0.92, 1])})`, opacity: enter }}>
        <svg width={620} height={600} viewBox="0 0 620 600">
          {arcs.map((a, i) =>
            a.drawnEnd > a.a0 ? (
              <path
                key={i}
                d={wedge(cx, cy, r, a.a0, a.drawnEnd)}
                fill={a.d.color}
                stroke="#0a0b0f"
                strokeWidth={4}
                transform={`translate(${a.dx} ${a.dy})`}
                style={a.d.hi ? { filter: `drop-shadow(0 0 22px ${accent}bb)` } : undefined}
              />
            ) : null
          )}
          {/* furo do donut */}
          <circle cx={cx} cy={cy} r={r * 0.5} fill="#0a0b0f" />
          <text x={cx} y={cy - 6} fill="#ffffff" fontFamily={DISPLAY} fontSize={62} textAnchor="middle">
            {Math.round((highlightedValue / total) * 100)}%
          </text>
          <text x={cx} y={cy + 34} fill="#9aa4b2" fontFamily={SANS} fontSize={22} textAnchor="middle">
            highlighted
          </text>
        </svg>

        {/* legenda */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {data.map((d, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, opacity: interpolate(frame, [20 + i * 6, 34 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
              <div style={{ width: 26, height: 26, borderRadius: 6, background: d.color, boxShadow: d.hi ? `0 0 16px ${accent}` : "none" }} />
              <div style={{ fontSize: 30, color: d.hi ? "#ffffff" : "#9aa4b2", fontWeight: d.hi ? 800 : 500 }}>
                {d.label}
              </div>
              <div style={{ fontSize: 30, color: d.color, fontWeight: 800, marginLeft: 6 }}>
                {Math.round((d.value / total) * 100)}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
