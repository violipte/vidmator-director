import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig, Easing } from "remotion";

// GROWING BAR CHART — barras verticais CRESCEM da esquerda p/ direita ao longo de anos;
// a última (finalBarYear) destacada com finalBarText em cima. Fundo grid escuro.
// Container do acervo VidMator (ref.: VidRush "Wish revenue → $1.9B"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const GrowingBarChart: React.FC<{
  title?: string;
  finalBarYear?: number;
  finalBarText?: string;
  accent?: string;
}> = ({
  title = "Wish revenue",
  finalBarYear = 2018,
  finalBarText = "$1.9B",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const N = 8;
  const years = Array.from({ length: N }, (_, i) => finalBarYear - (N - 1) + i);
  // trend crescente (curva suave até 1.0 no último ano)
  const heights = Array.from({ length: N }, (_, i) => {
    const t = i / (N - 1);
    return 0.14 + 0.86 * Math.pow(t, 1.7);
  });

  const W = 1560;
  const H = 720;
  const padL = 100;
  const padR = 80;
  const padB = 90;
  const padT = 120;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;
  const slot = innerW / N;
  const barW = slot * 0.56;

  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const enter = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 22 });

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
          marginBottom: 20,
        }}
      >
        {title}
      </div>

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ opacity: enter }}>
        {/* baseline */}
        <line x1={padL - 10} y1={padT + innerH} x2={W - padR + 10} y2={padT + innerH} stroke="#5b6472" strokeWidth={2} />

        {heights.map((h, i) => {
          const isLast = i === N - 1;
          const start = 12 + i * 6;
          const grow = interpolate(frame, [start, start + 34], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const bh = innerH * h * grow;
          const x = padL + slot * i + (slot - barW) / 2;
          const y = padT + innerH - bh;
          const color = isLast ? accent : "#334a63";
          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={bh}
                rx={8}
                fill={color}
                style={isLast ? { filter: `drop-shadow(0 0 22px ${accent}aa)` } : undefined}
              />
              {isLast && grow > 0.6 ? (
                <text
                  x={x + barW / 2}
                  y={y - 22}
                  fill="#ffffff"
                  fontFamily={DISPLAY}
                  fontSize={54}
                  textAnchor="middle"
                  style={{ filter: `drop-shadow(0 0 14px ${accent})` }}
                >
                  {finalBarText}
                </text>
              ) : null}
              <text x={x + barW / 2} y={padT + innerH + 44} fill={isLast ? accent : "#9aa4b2"} fontFamily={SANS} fontSize={26} fontWeight={isLast ? 800 : 500} textAnchor="middle">
                {years[i]}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
