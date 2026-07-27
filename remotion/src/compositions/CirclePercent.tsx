import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// CIRCLE PERCENT — anel/donut circular (SVG stroke-dashoffset) enchendo até `percent`%;
// número % grande no centro; título embaixo. Fundo grid escuro + glow âmbar.
// Container do acervo VidMator (ref.: VidRush "IMPORTED OIL 73%"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const CirclePercent: React.FC<{
  titleContent?: string;
  percent?: number;
  accent?: string;
}> = ({
  titleContent = "IMPORTED OIL",
  percent = 73,
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pct = Math.max(0, Math.min(100, percent));

  const fill = interpolate(frame, [12, 76], [0, pct], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 85 }, durationInFrames: 24 });
  const glow = 0.5 + 0.5 * Math.sin(frame / 13);
  const titleOp = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const cx = 300;
  const cy = 300;
  const r = 230;
  const frac = fill / 100;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0b0f",
        backgroundImage:
          "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        fontFamily: SANS,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${interpolate(enter, [0, 1], [0.9, 1])})` }}>
        <svg width={600} height={600} viewBox="0 0 600 600">
          {/* trilho */}
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={34} />
          {/* preenchimento */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={accent}
            strokeWidth={34}
            strokeLinecap="round"
            pathLength={1}
            strokeDasharray={1}
            strokeDashoffset={1 - frac}
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ filter: `drop-shadow(0 0 ${14 + glow * 18}px ${accent})` }}
          />
          <text
            x={cx}
            y={cy + 34}
            fill="#ffffff"
            fontFamily={DISPLAY}
            fontSize={168}
            textAnchor="middle"
            style={{ filter: `drop-shadow(0 0 ${18 + glow * 20}px ${accent})` }}
          >
            {Math.round(fill)}
            <tspan fontSize={90} fill={accent}>%</tspan>
          </text>
        </svg>

        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 66,
            letterSpacing: 3,
            color: "#ffffff",
            textTransform: "uppercase",
            marginTop: 24,
            opacity: titleOp,
            textShadow: `0 0 22px ${accent}66`,
          }}
        >
          {titleContent}
        </div>
      </div>
    </AbsoluteFill>
  );
};
