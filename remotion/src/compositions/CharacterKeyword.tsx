import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// CHARACTER KEYWORD — retrato recortado + UMA keyword grande surgindo com glow accent.
// Container do acervo VidMator (ref.: VidRush "keyword stamp"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const CharacterKeyword: React.FC<{
  characterImage?: string;
  keyword?: string;
  accent?: string;
}> = ({
  characterImage = "test/people/pessoa_2.png",
  keyword = "Legacy",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const portrIn = spring({ frame, fps, config: { damping: 18, stiffness: 80 }, durationInFrames: 22 });
  const wordE = spring({ frame: frame - 14, fps, config: { damping: 12, stiffness: 120 }, durationInFrames: 20 });
  const wordScale = interpolate(wordE, [0, 1], [0.6, 1]);
  const wordOp = interpolate(frame, [14, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 12);
  const kw = (keyword || "").toUpperCase();

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", opacity: outOp, overflow: "hidden", fontFamily: SANS }}>
      {/* grade sutil */}
      <AbsoluteFill
        style={{
          background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
          maskImage: "radial-gradient(ellipse 80% 80% at 50% 50%, black 40%, transparent 90%)",
        }}
      />
      {/* halo accent atrás */}
      <AbsoluteFill style={{ background: `radial-gradient(60% 75% at 70% 50%, ${accent}22 0%, transparent 55%)` }} />

      {/* retrato recortado à esquerda */}
      <Img
        src={staticFile(characterImage)}
        style={{
          position: "absolute",
          left: "4%",
          bottom: 0,
          height: "102%",
          objectFit: "contain",
          objectPosition: "bottom center",
          filter: "drop-shadow(0 12px 36px rgba(0,0,0,0.7)) contrast(1.05)",
          opacity: portrIn,
          transform: `translateX(${(1 - portrIn) * -80}px)`,
        }}
      />

      {/* keyword grande à direita, com glow */}
      <div
        style={{
          position: "absolute",
          right: "5%",
          top: "50%",
          width: "56%",
          textAlign: "right",
          transform: `translateY(-50%) scale(${wordScale})`,
          transformOrigin: "right center",
          opacity: wordOp,
        }}
      >
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 200,
            lineHeight: 0.92,
            color: "#ffffff",
            letterSpacing: -2,
            textShadow: `0 0 ${28 + glow * 30}px ${accent}, 0 0 ${64 + glow * 44}px ${accent}88, 0 12px 40px rgba(0,0,0,0.7)`,
          }}
        >
          {kw}
        </div>
        <div
          style={{
            width: "60%",
            height: 6,
            marginLeft: "auto",
            marginTop: 26,
            background: `linear-gradient(90deg, transparent, ${accent})`,
            boxShadow: `0 0 18px ${accent}`,
            opacity: wordOp,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
