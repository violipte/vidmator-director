import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";

// LINE CHART — N linhas DESENHANDO (stroke-dashoffset) num grid; eixos com anos
// (startValue..endValue); pattern exponential/linear muda a curva. Fundo grid escuro.
// Container do acervo VidMator. Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";
const PALETTE = ["#38bdf8", "#a78bfa", "#34d399", "#f472b6"];

export const LineChart: React.FC<{
  chartTitle?: string;
  numberOfLines?: number;
  dataPoints?: number;
  startValue?: number;
  endValue?: number;
  pattern?: "exponential" | "linear";
  accent?: string;
}> = ({
  chartTitle = "Chart Title Here",
  numberOfLines = 3,
  dataPoints = 8,
  startValue = 1990,
  endValue = 2023,
  pattern = "exponential",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();

  // plot area
  const W = 1520;
  const H = 720;
  const padL = 120;
  const padR = 60;
  const padT = 40;
  const padB = 90;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const nLines = Math.max(1, numberOfLines);
  const nPts = Math.max(2, dataPoints);

  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  // dados determinísticos por linha
  const lines = Array.from({ length: nLines }, (_, li) => {
    const color = li === 0 ? accent : PALETTE[(li - 1) % PALETTE.length];
    const base = 0.55 + 0.28 * Math.sin(li * 1.7); // amplitude por linha
    const pts = Array.from({ length: nPts }, (_, pi) => {
      const t = pi / (nPts - 1);
      const shape = pattern === "exponential" ? (Math.exp(t * 2.1) - 1) / (Math.exp(2.1) - 1) : t;
      const wiggle = 0.05 * Math.sin(pi * 1.3 + li * 2.0);
      const yFrac = Math.max(0.02, Math.min(0.98, shape * base + 0.06 + li * 0.05 + wiggle));
      const x = padL + t * innerW;
      const y = padT + innerH - yFrac * innerH;
      return { x, y };
    });
    const d = "M " + pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" L ");
    return { color, pts, d };
  });

  const years = Array.from({ length: nPts }, (_, i) => Math.round(startValue + ((endValue - startValue) * i) / (nPts - 1)));
  const gridRows = 5;

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
          fontSize: 62,
          color: "#ffffff",
          opacity: titleOp,
          transform: `translateY(${interpolate(titleOp, [0, 1], [-20, 0])}px)`,
          marginBottom: 24,
        }}
      >
        {chartTitle}
      </div>

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {/* grid horizontal */}
        {Array.from({ length: gridRows + 1 }, (_, i) => {
          const y = padT + (innerH * i) / gridRows;
          return <line key={`h${i}`} x1={padL} y1={y} x2={W - padR} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />;
        })}
        {/* eixos */}
        <line x1={padL} y1={padT} x2={padL} y2={padT + innerH} stroke="#5b6472" strokeWidth={2} />
        <line x1={padL} y1={padT + innerH} x2={W - padR} y2={padT + innerH} stroke="#5b6472" strokeWidth={2} />

        {/* linhas desenhando */}
        {lines.map((ln, li) => {
          const start = 14 + li * 8;
          const p = interpolate(frame, [start, start + 60], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const last = ln.pts[ln.pts.length - 1];
          return (
            <g key={li}>
              <path
                d={ln.d}
                fill="none"
                stroke={ln.color}
                strokeWidth={5}
                strokeLinecap="round"
                strokeLinejoin="round"
                pathLength={1}
                strokeDasharray={1}
                strokeDashoffset={1 - p}
                style={{ filter: `drop-shadow(0 0 8px ${ln.color}88)` }}
              />
              {p > 0.98 ? <circle cx={last.x} cy={last.y} r={8} fill={ln.color} style={{ filter: `drop-shadow(0 0 10px ${ln.color})` }} /> : null}
            </g>
          );
        })}

        {/* anos no eixo X */}
        {years.map((yr, i) => {
          const x = padL + (innerW * i) / (nPts - 1);
          return (
            <text key={i} x={x} y={padT + innerH + 40} fill="#9aa4b2" fontFamily={SANS} fontSize={26} textAnchor="middle">
              {yr}
            </text>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
