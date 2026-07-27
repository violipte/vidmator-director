import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// CIRCLE HIGHLIGHT — imagem full; um CÍRCULO (accent/vermelho) é DESENHADO (stroke-dashoffset)
// ao redor de uma região; label do nome aparece embaixo (slide-up). Container do acervo VidMator.
const SANS = "'Inter', 'Segoe UI', sans-serif";
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

export const CircleHighlight: React.FC<{
  image?: string;
  label?: string;
  accent?: string;
}> = ({
  image = "jobs/motos2/clips/moto0.jpg",
  label = "Dr. James Mitchell",
  accent = "#dc2626",
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const imgOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const imgScale = interpolate(frame, [0, 150], [1.06, 1.0], { extrapolateRight: "clamp" });

  // círculo na região central-superior (destaque de rosto/objeto)
  const cx = width * 0.5;
  const cy = height * 0.42;
  const rx = 260;
  const ry = 300;
  const circ = 2 * Math.PI * ((rx + ry) / 2);                          // perímetro aprox. da elipse
  const draw = interpolate(frame, [18, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const labelOp = interpolate(frame, [50, 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelY = interpolate(frame, [50, 66], [30, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden", fontFamily: SANS }}>
      <Img
        src={staticFile(image)}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: imgOp,
          transform: `scale(${imgScale})`,
        }}
      />
      {/* leve escurecimento p/ legibilidade do label */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.15) 0%, transparent 30%, rgba(0,0,0,0.55) 100%)" }} />

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <ellipse
          cx={cx}
          cy={cy}
          rx={rx}
          ry={ry}
          fill="none"
          stroke={accent}
          strokeWidth={9}
          strokeLinecap="round"
          transform={`rotate(-8 ${cx} ${cy})`}
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - draw)}
          style={{ filter: `drop-shadow(0 0 12px ${accent}cc)` }}
        />
      </svg>

      {/* label do nome embaixo */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 110,
          textAlign: "center",
          opacity: labelOp,
          transform: `translateY(${labelY}px)`,
        }}
      >
        <div style={{ display: "inline-block", background: accent, padding: "18px 44px", borderRadius: 10, boxShadow: "0 14px 40px rgba(0,0,0,0.6)" }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 56, fontWeight: 900, color: "#fff", letterSpacing: 1 }}>{label}</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
