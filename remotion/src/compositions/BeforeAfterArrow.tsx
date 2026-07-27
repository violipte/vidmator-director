import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// BEFORE / AFTER ARROW — foto "antes" (dessaturada/P&B) à esq → SETA accent no centro → "depois" (cor) à dir.
// Container do acervo VidMator (ref.: VidRush transformação/upgrade). Niche-agnostic via props.
// Entrada sequencial: painel BEFORE → seta → painel AFTER, labels BEFORE/AFTER.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const BeforeAfterArrow: React.FC<{
  beforeImage?: string;
  afterImage?: string;
  accent?: string;
}> = ({
  beforeImage = "test/people/pessoa_1.png",
  afterImage = "test/people/pessoa_4.png",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const beforeIn = spring({ frame, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 22 });
  const arrowIn = spring({ frame: frame - 20, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 18 });
  const afterIn = spring({ frame: frame - 34, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 22 });
  const glow = 0.5 + 0.5 * Math.sin(frame / 12);
  const arrowPush = interpolate(arrowIn, [0, 1], [-40, 0]);

  const panel = (prog: number, gray: boolean, fromLeft: boolean): React.CSSProperties => ({
    position: "relative",
    width: 620,
    height: 700,
    borderRadius: 16,
    overflow: "hidden",
    background: "#14161c",
    border: gray ? "1px solid rgba(255,255,255,0.10)" : `2px solid ${accent}`,
    boxShadow: gray ? "0 20px 60px rgba(0,0,0,0.6)" : `0 20px 60px rgba(0,0,0,0.6), 0 0 ${34 * prog}px ${accent}66`,
    opacity: prog,
    transform: `translateX(${(1 - prog) * (fromLeft ? -90 : 90)}px) scale(${0.92 + 0.08 * prog})`,
  });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 40%, #14161c 0%, #0a0b0f 70%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      {/* grade sutil */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
        {/* BEFORE */}
        <div style={panel(beforeIn, true, true)}>
          <Img
            src={staticFile(beforeImage)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
              filter: "grayscale(1) contrast(1.05) brightness(0.86)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 24,
              left: 24,
              padding: "8px 20px",
              borderRadius: 8,
              background: "rgba(0,0,0,0.6)",
              color: "#cfd6df",
              fontFamily: DISPLAY,
              fontSize: 30,
              letterSpacing: 3,
            }}
          >
            BEFORE
          </div>
        </div>

        {/* SETA accent */}
        <div style={{ opacity: arrowIn, transform: `translateX(${arrowPush}px) scale(${0.6 + 0.4 * arrowIn})` }}>
          <svg width="180" height="120" viewBox="0 0 180 120">
            <defs>
              <linearGradient id="baArrow" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor={accent} stopOpacity="0.5" />
                <stop offset="100%" stopColor={accent} stopOpacity="1" />
              </linearGradient>
            </defs>
            <g
              style={{
                filter: `drop-shadow(0 0 ${10 + glow * 16}px ${accent})`,
              }}
            >
              <rect x="6" y="46" width="118" height="28" rx="8" fill="url(#baArrow)" />
              <path d="M112 20 L172 60 L112 100 Z" fill={accent} />
            </g>
          </svg>
        </div>

        {/* AFTER */}
        <div style={panel(afterIn, false, false)}>
          <Img
            src={staticFile(afterImage)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
              filter: "saturate(1.15) contrast(1.06) brightness(1.03)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 24,
              right: 24,
              padding: "8px 20px",
              borderRadius: 8,
              background: accent,
              color: "#0a0b0f",
              fontFamily: DISPLAY,
              fontSize: 30,
              letterSpacing: 3,
              boxShadow: `0 0 ${18 * afterIn}px ${accent}`,
            }}
          >
            AFTER
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
