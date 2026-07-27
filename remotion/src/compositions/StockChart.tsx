import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig, Easing } from "remotion";

// STOCK CHART — linha estilo bolsa subindo com área preenchida (gradiente accent), desenhando;
// grid; título. Fundo grid escuro. Container do acervo VidMator. Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const StockChart: React.FC<{
  title?: string;
  accent?: string;
}> = ({
  title = "Stock Growth",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const W = 1560;
  const H = 760;
  const padL = 90;
  const padR = 70;
  const padT = 50;
  const padB = 80;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  // série com tendência de alta + volatilidade determinística (candles-like)
  const N = 22;
  const pts = Array.from({ length: N }, (_, i) => {
    const t = i / (N - 1);
    const trend = Math.pow(t, 1.25);
    const noise = 0.05 * Math.sin(i * 1.9) + 0.03 * Math.sin(i * 0.7);
    const yFrac = Math.max(0.04, Math.min(0.96, 0.1 + 0.82 * trend + noise));
    const x = padL + t * innerW;
    const y = padT + innerH - yFrac * innerH;
    return { x, y };
  });
  const linePath = "M " + pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" L ");
  const last = pts[pts.length - 1];
  const first = pts[0];
  const areaPath = `${linePath} L ${last.x.toFixed(1)} ${(padT + innerH).toFixed(1)} L ${first.x.toFixed(1)} ${(padT + innerH).toFixed(1)} Z`;

  const draw = interpolate(frame, [12, 84], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const areaOp = interpolate(frame, [30, 80], [0, 0.9], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const enter = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 22 });
  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const gridRows = 5;
  const gridCols = 6;

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
          marginBottom: 18,
          textShadow: `0 0 22px ${accent}55`,
        }}
      >
        {title}
      </div>

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ opacity: enter }}>
        <defs>
          <linearGradient id="stockArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accent} stopOpacity={0.55} />
            <stop offset="100%" stopColor={accent} stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* grid */}
        {Array.from({ length: gridRows + 1 }, (_, i) => {
          const y = padT + (innerH * i) / gridRows;
          return <line key={`h${i}`} x1={padL} y1={y} x2={W - padR} y2={y} stroke="rgba(255,255,255,0.07)" strokeWidth={1} />;
        })}
        {Array.from({ length: gridCols + 1 }, (_, i) => {
          const x = padL + (innerW * i) / gridCols;
          return <line key={`v${i}`} x1={x} y1={padT} x2={x} y2={padT + innerH} stroke="rgba(255,255,255,0.05)" strokeWidth={1} />;
        })}
        {/* eixos */}
        <line x1={padL} y1={padT + innerH} x2={W - padR} y2={padT + innerH} stroke="#5b6472" strokeWidth={2} />

        {/* área */}
        <path d={areaPath} fill="url(#stockArea)" opacity={areaOp} />

        {/* linha desenhando */}
        <path
          d={linePath}
          fill="none"
          stroke={accent}
          strokeWidth={6}
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - draw}
          style={{ filter: `drop-shadow(0 0 12px ${accent}cc)` }}
        />

        {/* ponto de topo */}
        {draw > 0.98 ? (
          <>
            <circle cx={last.x} cy={last.y} r={11} fill={accent} style={{ filter: `drop-shadow(0 0 14px ${accent})` }} />
            <circle cx={last.x} cy={last.y} r={20} fill="none" stroke={accent} strokeWidth={2} opacity={0.5} />
          </>
        ) : null}
      </svg>
    </AbsoluteFill>
  );
};
