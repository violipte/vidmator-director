import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// NUMBER COUNT OVERLAY — número GIGANTE contando de 0 até `value` (separador de milhar) + label;
// glow âmbar. Fundo semi-transparente (pensado p/ overlay sobre vídeo). Niche-agnostic via props.
// Container do acervo VidMator (ref.: VidRush "2,500,000+ TRUCKS IN SERVICE").
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";
const thousands = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

export const NumberCountOverlay: React.FC<{
  label?: string;
  value?: number;
  prefix?: string;
  suffix?: string;
  accent?: string;
}> = ({
  label = "TRUCKS IN SERVICE",
  value = 2500000,
  prefix = "",
  suffix = "+",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const current = interpolate(frame, [10, 82], [0, value], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 95 }, durationInFrames: 20 });
  const scale = interpolate(enter, [0, 1], [1.25, 1]);
  const glow = 0.5 + 0.5 * Math.sin(frame / 12);
  const labelOp = interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const display = prefix + thousands(current) + suffix;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(60% 55% at 50% 50%, ${accent}18 0%, rgba(6,7,10,0.72) 55%, rgba(6,7,10,0.9) 100%)`,
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <div style={{ textAlign: "center", transform: `scale(${scale})`, opacity: interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" }) }}>
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 240,
            lineHeight: 1,
            color: "#ffffff",
            letterSpacing: 2,
            textShadow: `0 0 ${30 + glow * 34}px ${accent}, 0 0 ${72 + glow * 50}px ${accent}88`,
          }}
        >
          {display}
        </div>
        <div
          style={{
            marginTop: 26,
            fontFamily: DISPLAY,
            fontSize: 58,
            letterSpacing: 6,
            color: accent,
            textTransform: "uppercase",
            opacity: labelOp,
            transform: `translateY(${interpolate(labelOp, [0, 1], [18, 0])}px)`,
          }}
        >
          {label}
        </div>
      </div>
    </AbsoluteFill>
  );
};
