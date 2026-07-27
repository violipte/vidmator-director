import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// IMAGE TEXT ANNOTATION — objeto ao centro sobre fundo verde-escuro; para cada label uma TAG
// ancorada em (x%,y%) com LINHA LÍDER (SVG) até um ponto na imagem. Aparecem 1 a 1.
// Container do acervo VidMator (ref.: VidRush "peças anotadas"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

type Label = { text: string; x: number; y: number };

export const ImageTextAnnotation: React.FC<{
  image?: string;
  labels?: Label[];
  accent?: string;
}> = ({
  image = "jobs/motos2/clips/moto20.jpg",
  labels = [
    { text: "Ladder-Frame", x: 50, y: 14 },
    { text: "Thick Gusset", x: 26, y: 82 },
    { text: "Weld Beads", x: 74, y: 82 },
  ],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const imgIn = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 24 });
  const STAGGER = 18;
  const START = 20;

  // âncora da tag (borda) → ponto na imagem (centro do frame do objeto).
  // A imagem ocupa uma moldura central; converto x%,y% (do frame) p/ px absolutos do canvas.
  const toPx = (x: number, y: number) => ({ px: (x / 100) * width, py: (y / 100) * height });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(130% 110% at 50% 30%, #14322a 0%, #0c1f1a 55%, #06110e 100%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      {/* grade sutil */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 64px)",
        }}
      />

      {/* imagem do objeto, moldura central */}
      <div
        style={{
          position: "relative",
          width: 1120,
          height: 720,
          borderRadius: 16,
          overflow: "hidden",
          border: "3px solid rgba(255,255,255,0.14)",
          boxShadow: "0 24px 70px rgba(0,0,0,0.65)",
          opacity: imgIn,
          transform: `scale(${0.94 + 0.06 * imgIn})`,
        }}
      >
        <Img
          src={staticFile(image)}
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: "contrast(1.05) saturate(1.05)" }}
        />
      </div>

      {/* SVG overlay: linhas líderes + pontos */}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        {labels.slice(0, 6).map((lab, i) => {
          const appear = START + i * STAGGER;
          const p = interpolate(frame, [appear, appear + 16], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const target = toPx(lab.x, lab.y);
          // ponto de âncora da tag: puxa p/ borda mais próxima horizontalmente
          const tagOnLeft = lab.x < 45;
          const tagOnRight = lab.x > 55;
          const anchorX = tagOnLeft ? target.px - 210 : tagOnRight ? target.px + 210 : target.px;
          const anchorY = lab.y < 45 ? target.py - 120 : target.py + 120;
          const drawX = interpolate(p, [0, 1], [target.px, anchorX]);
          const drawY = interpolate(p, [0, 1], [target.py, anchorY]);
          return (
            <g key={i}>
              <line
                x1={target.px}
                y1={target.py}
                x2={drawX}
                y2={drawY}
                stroke={accent}
                strokeWidth={3}
                strokeDasharray="2 6"
                strokeLinecap="round"
                opacity={p}
              />
              <circle cx={target.px} cy={target.py} r={7} fill={accent} opacity={p} />
              <circle cx={target.px} cy={target.py} r={13} fill="none" stroke={accent} strokeWidth={2} opacity={p * 0.5} />
            </g>
          );
        })}
      </svg>

      {/* tags HTML posicionadas */}
      {labels.slice(0, 6).map((lab, i) => {
        const appear = START + i * STAGGER;
        const tp = spring({ frame: frame - appear, fps, config: { damping: 15, stiffness: 130 }, durationInFrames: 16 });
        const tagOnLeft = lab.x < 45;
        const tagOnRight = lab.x > 55;
        const target = toPx(lab.x, lab.y);
        const anchorX = tagOnLeft ? target.px - 210 : tagOnRight ? target.px + 210 : target.px;
        const anchorY = lab.y < 45 ? target.py - 120 : target.py + 120;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: anchorX,
              top: anchorY,
              transform: `translate(-50%,-50%) scale(${0.6 + 0.4 * tp})`,
              opacity: tp,
              padding: "12px 22px",
              borderRadius: 12,
              background: accent,
              color: "#0a0b0f",
              fontFamily: DISPLAY,
              fontSize: 30,
              letterSpacing: 1,
              whiteSpace: "nowrap",
              boxShadow: `0 8px 24px rgba(0,0,0,0.5), 0 0 18px ${accent}55`,
            }}
          >
            {lab.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
