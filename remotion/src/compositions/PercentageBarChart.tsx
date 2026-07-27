import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// PERCENTAGE BAR CHART — barra VERTICAL num contorno que ENCHE de baixo p/ cima até `percentage`%.
// Número % gigante ao lado com glow âmbar; título no topo; fundo grid escuro.
// Container do acervo VidMator (ref.: VidRush "TOTAL NATURAL GAS 49%"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const PercentageBarChart: React.FC<{
  titleText?: string;
  bottomText?: string;
  percentage?: number;
  accent?: string;
}> = ({
  titleText = "TOTAL NATURAL GAS",
  bottomText = "",
  percentage = 49,
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pct = Math.max(0, Math.min(100, percentage));
  const fill = interpolate(frame, [12, 74], [0, pct], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 24 });
  const titleOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 13);

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
          fontSize: 72,
          letterSpacing: 2,
          color: "#ffffff",
          textTransform: "uppercase",
          opacity: titleOp,
          transform: `translateY(${interpolate(titleOp, [0, 1], [-24, 0])}px)`,
          marginBottom: 60,
          textAlign: "center",
        }}
      >
        {titleText}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 90, transform: `scale(${interpolate(enter, [0, 1], [0.9, 1])})` }}>
        {/* tubo/contorno vertical */}
        <div
          style={{
            position: "relative",
            width: 170,
            height: 620,
            borderRadius: 18,
            border: `3px solid ${accent}66`,
            background: "rgba(255,255,255,0.02)",
            overflow: "hidden",
            boxShadow: `0 0 ${18 + glow * 22}px ${accent}44, inset 0 0 40px rgba(0,0,0,0.6)`,
          }}
        >
          {/* marcações internas */}
          {[25, 50, 75].map((m) => (
            <div key={m} style={{ position: "absolute", left: 0, right: 0, bottom: `${m}%`, height: 1, background: "rgba(255,255,255,0.08)" }} />
          ))}
          {/* preenchimento */}
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 0,
              height: `${fill}%`,
              background: `linear-gradient(180deg, ${accent} 0%, ${accent}cc 60%, ${accent}88 100%)`,
              boxShadow: `0 0 40px ${accent}, 0 -6px 24px ${accent}aa`,
              borderTop: "2px solid rgba(255,255,255,0.6)",
            }}
          />
        </div>

        {/* número % */}
        <div style={{ textAlign: "left" }}>
          <div
            style={{
              fontFamily: DISPLAY,
              fontSize: 260,
              lineHeight: 0.9,
              color: "#ffffff",
              textShadow: `0 0 ${28 + glow * 30}px ${accent}, 0 0 ${64 + glow * 44}px ${accent}88`,
            }}
          >
            {Math.round(fill)}
            <span style={{ fontSize: 130, color: accent }}>%</span>
          </div>
          {bottomText ? (
            <div style={{ marginTop: 10, fontSize: 34, color: "#9aa4b2", letterSpacing: 1 }}>{bottomText}</div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
