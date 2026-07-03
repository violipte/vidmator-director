import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// Card de PESSOA histórica: retrato PD recortado (rembg) + nome grande estilo sticker.
// Branch "Real (entidade=pessoa)" do diretor inteligente.

type Props = {
  nome?: string;
  imagem_rel?: string;
  subtitulo?: string | null;   // ex: "Naturalista · 1809–1882"
  fundo?: "claro" | "escuro";
  durFrames?: number;
  headFont?: string;           // fonte do nome (tema por niche)
  uiFont?: string;             // fonte do subtítulo
};

export const PersonCard: React.FC<Props> = ({
  nome = "CHARLES DARWIN", imagem_rel = "test/people/darwin.png",
  subtitulo = "Naturalista · 1809–1882", fundo = "claro", durFrames,
  headFont = "'Arial Black', 'Segoe UI', system-ui, sans-serif",
  uiFont = "'Segoe UI', system-ui, sans-serif",
}) => {
  const frame = useCurrentFrame();
  const cfg = useVideoConfig();
  const fps = cfg.fps;
  const total = durFrames || cfg.durationInFrames;

  const portrIn = spring({ frame, fps, config: { damping: 16 }, durationInFrames: 18 });
  const nameIn = spring({ frame: frame - 8, fps, config: { damping: 14 }, durationInFrames: 20 });
  const subIn = interpolate(frame - 22, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outOp = interpolate(frame, [total - 12, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const dark = fundo === "escuro";
  const bg = dark ? "#0e131c" : "#efe6c9";
  const gridC = dark ? "rgba(120,150,200,0.07)" : "rgba(120,100,55,0.13)";
  const nameUp = (nome || "").toUpperCase();
  const fontSize = Math.min(150, Math.max(70, 1240 / Math.max(7, nameUp.length * 0.6)));
  const nameColor = dark ? "#f4f7fb" : "#ffffff";
  const shadow = dark
    ? "0 8px 22px rgba(0,0,0,0.6), 5px 5px 0 rgba(0,0,0,0.55)"
    : "0 8px 18px rgba(60,45,20,0.35), 5px 5px 0 rgba(60,45,20,0.35)";

  return (
    <AbsoluteFill style={{ backgroundColor: bg, opacity: outOp, overflow: "hidden" }}>
      {/* grid de fundo */}
      <AbsoluteFill style={{
        backgroundImage: `linear-gradient(${gridC} 1px, transparent 1px), linear-gradient(90deg, ${gridC} 1px, transparent 1px)`,
        backgroundSize: "48px 48px", maskImage: "radial-gradient(ellipse at 60% 50%, black 55%, transparent 100%)",
      }} />

      {/* retrato recortado, ancorado embaixo à esquerda */}
      <Img src={staticFile(imagem_rel)} style={{
        position: "absolute", left: 60, bottom: 0, height: "100%", objectFit: "contain", objectPosition: "bottom left",
        filter: `drop-shadow(24px 10px 30px rgba(0,0,0,${dark ? 0.5 : 0.28})) contrast(1.04) saturate(1.05)`,
        opacity: portrIn, transform: `translateX(${(1 - portrIn) * -70}px)`,
      }} />

      {/* nome (sticker) + subtítulo, à direita */}
      <div style={{
        position: "absolute", right: 70, top: "50%", width: "58%", textAlign: "right",
        transform: `translateY(-50%) translateX(${(1 - nameIn) * 80}px) scale(${0.9 + 0.1 * nameIn})`, opacity: nameIn,
      }}>
        <div style={{
          fontFamily: headFont, fontWeight: 900,
          fontSize, lineHeight: 1.0, letterSpacing: 1, color: nameColor, textShadow: shadow,
          WebkitTextStroke: dark ? "0px" : "0px",
        }}>{nameUp}</div>
        {subtitulo && (
          <div style={{
            marginTop: 18, fontFamily: uiFont, fontWeight: 700, fontSize: 30,
            letterSpacing: 2, color: dark ? "#9fb2cc" : "#7a6532", opacity: subIn, textTransform: "uppercase",
          }}>{subtitulo}</div>
        )}
      </div>
    </AbsoluteFill>
  );
};
