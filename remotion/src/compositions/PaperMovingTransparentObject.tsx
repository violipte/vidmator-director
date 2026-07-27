import { AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// PAPER MOVING TRANSPARENT OBJECT — fundo de PAPEL (textura clara + leve parallax) + recorte
// transparente (PNG alpha) flutuando; leve grão via staticFile("grain.png").
// Container do acervo VidMator (ref.: VidRush "objeto sobre papel/scrapbook"). Niche-agnostic via props.
const SANS = "'Inter','Segoe UI',sans-serif";

export const PaperMovingTransparentObject: React.FC<{
  object?: string;
  accent?: string;
}> = ({
  object = "test/people/pessoa_0.png",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const objIn = spring({ frame, fps, config: { damping: 18, stiffness: 70 }, durationInFrames: 26 });
  // flutuação suave do objeto + leve rotação
  const floatY = Math.sin(frame / 26) * 20;
  const floatX = Math.cos(frame / 34) * 14;
  const tilt = Math.sin(frame / 40) * 2.2;
  // parallax leve do papel (contra-movimento)
  const paperX = Math.cos(frame / 34) * -8;
  const paperY = Math.sin(frame / 26) * -6;
  // grão animado
  const gx = (frame * 53) % 600;
  const gy = (frame * 31) % 600;

  return (
    <AbsoluteFill style={{ overflow: "hidden", fontFamily: SANS, background: "#e9e2d0" }}>
      {/* PAPEL: base creme + textura fibrosa + manchas suaves, com parallax */}
      <AbsoluteFill
        style={{
          transform: `translate(${paperX}px, ${paperY}px) scale(1.06)`,
          background:
            "radial-gradient(120% 120% at 30% 20%, #f7f1e2 0%, #ece4d1 45%, #ddd2ba 100%)",
        }}
      >
        {/* fibras/ruído do papel via gradientes finos cruzados */}
        <AbsoluteFill
          style={{
            opacity: 0.5,
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(120,100,60,0.05) 0 1px, transparent 1px 3px), repeating-linear-gradient(90deg, rgba(120,100,60,0.05) 0 1px, transparent 1px 3px)",
          }}
        />
        {/* manchas / envelhecimento */}
        <AbsoluteFill
          style={{
            backgroundImage:
              "radial-gradient(circle at 78% 30%, rgba(150,120,70,0.14) 0%, transparent 24%), radial-gradient(circle at 18% 78%, rgba(150,120,70,0.12) 0%, transparent 22%), radial-gradient(circle at 55% 60%, rgba(120,90,50,0.08) 0%, transparent 30%)",
          }}
        />
        {/* vinheta do papel */}
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(90,70,40,0.28) 100%)" }} />
      </AbsoluteFill>

      {/* sombra projetada do objeto no papel */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 520,
          height: 120,
          transform: `translate(-50%, 260px) translate(${floatX * 1.4}px, 0) scale(${0.7 + 0.3 * objIn})`,
          background: "radial-gradient(ellipse at center, rgba(60,45,25,0.32) 0%, transparent 70%)",
          filter: "blur(8px)",
          opacity: objIn * 0.8,
        }}
      />

      {/* objeto transparente flutuando */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Img
          src={staticFile(object)}
          style={{
            height: "82%",
            objectFit: "contain",
            transform: `translate(${floatX}px, ${floatY - (1 - objIn) * 40}px) rotate(${tilt}deg) scale(${0.9 + 0.1 * objIn})`,
            opacity: objIn,
            filter: `drop-shadow(0 24px 34px rgba(60,45,25,0.4)) drop-shadow(0 0 30px ${accent}22)`,
          }}
        />
      </AbsoluteFill>

      {/* faixa de luz quente (leve toque do accent) */}
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          mixBlendMode: "soft-light",
          background: `radial-gradient(circle at ${60 + Math.sin(frame / 60) * 8}% 22%, ${accent}55 0%, transparent 46%)`,
        }}
      />

      {/* grão por cima */}
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          mixBlendMode: "multiply",
          opacity: 0.12,
          backgroundImage: `url(${staticFile("grain.png")})`,
          backgroundRepeat: "repeat",
          backgroundSize: "540px 540px",
          backgroundPosition: `${gx}px ${gy}px`,
        }}
      />
    </AbsoluteFill>
  );
};
