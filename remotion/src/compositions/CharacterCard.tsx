import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// CHARACTER CARD — retrato recortado (PNG alpha) sobre fundo escuro dramático + nome grande + subtítulo.
// Container do acervo VidMator (ref.: VidRush "character intro"). Niche-agnostic via props com defaults.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const CharacterCard: React.FC<{
  characterImage?: string;
  title?: string;
  subtitle?: string;
  accent?: string;
}> = ({
  characterImage = "test/people/pessoa_2.png",
  title = "Franjo Tudjman",
  subtitle = "President of Croatia",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const portrIn = spring({ frame, fps, config: { damping: 18, stiffness: 80 }, durationInFrames: 24 });
  const nameIn = spring({ frame: frame - 10, fps, config: { damping: 15 }, durationInFrames: 22 });
  const subIn = interpolate(frame - 24, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 16);

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", opacity: outOp, overflow: "hidden", fontFamily: SANS }}>
      {/* halo dramático atrás do personagem */}
      <AbsoluteFill style={{ background: `radial-gradient(70% 80% at 32% 55%, ${accent}22 0%, transparent 55%)` }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 50%, transparent 45%, rgba(0,0,0,0.7) 100%)" }} />

      {/* retrato recortado, ancorado embaixo à esquerda */}
      <Img
        src={staticFile(characterImage)}
        style={{
          position: "absolute",
          left: "6%",
          bottom: 0,
          height: "104%",
          objectFit: "contain",
          objectPosition: "bottom center",
          filter: `drop-shadow(0 14px 40px rgba(0,0,0,0.7)) contrast(1.05) saturate(1.05)`,
          opacity: portrIn,
          transform: `translateY(${(1 - portrIn) * 60}px) scale(${0.94 + 0.06 * portrIn})`,
        }}
      />

      {/* bloco de texto à direita */}
      <div
        style={{
          position: "absolute",
          right: "7%",
          top: "50%",
          width: "48%",
          textAlign: "right",
          transform: `translateY(-50%) translateX(${(1 - nameIn) * 90}px)`,
          opacity: nameIn,
        }}
      >
        <div
          style={{
            width: 120,
            height: 4,
            marginLeft: "auto",
            marginBottom: 22,
            background: accent,
            boxShadow: `0 0 ${14 + glow * 14}px ${accent}`,
          }}
        />
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 108,
            lineHeight: 0.98,
            color: "#ffffff",
            letterSpacing: -1,
            textShadow: "0 10px 34px rgba(0,0,0,0.7)",
          }}
        >
          {title}
        </div>
        <div
          style={{
            marginTop: 20,
            fontSize: 38,
            fontWeight: 600,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: accent,
            opacity: subIn,
          }}
        >
          {subtitle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
