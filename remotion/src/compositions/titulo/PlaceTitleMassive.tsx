import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

/* PlaceTitleMassive — abertura dramática: o NOME DO LUGAR em letras gigantes
   atravessando a tela inteira por cima do footage aéreo (06/08, referência do Piter).

   Duas decisões que fazem o efeito:
   1. `mixBlendMode: overlay` — as letras se COMEM com a imagem (claras no céu,
      escuras na terra). Não é texto branco por cima.
   2. SVG com `textLength` + `lengthAdjust="spacingAndGlyphs"` — a palavra ocupa a
      largura EXATA pedida seja ela qual for ("AUSTRALIA", "BRAZIL", "THE AMAZON"),
      sem depender de qual fonte o Chrome do render acabou escolhendo. Medir por
      métrica de fonte (chute de razão largura/altura) errou feio no 1º teste.

   props: { texto, sub?, extravasa? (1.06 = sangra 3% de cada lado), altura? } */

type P = { texto?: string; sub?: string; extravasa?: number; altura?: number };

export const PlaceTitleMassive: React.FC<P> = ({
  texto = "", sub = "", extravasa = 1.06, altura = 0.30,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const palavra = (texto || "").toUpperCase().trim();

  const larguraTexto = width * extravasa;
  const fonte = height * altura;
  const baseline = height * 0.035 + fonte * 0.74;   // topo das maiúsculas quase no 0

  const t = frame / fps;
  const dur = durationInFrames / fps;
  const subida = interpolate(t, [0, 1.2], [height * 0.05, 0],
    { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const escala = interpolate(t, [0, dur], [1.05, 1.0], { extrapolateRight: "clamp" });
  const opac = interpolate(t, [0, 0.6, dur - 0.5, dur], [0, 1, 1, 0.9],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blur = interpolate(t, [0, 1.0], [16, 0],
    { extrapolateRight: "clamp", easing: Easing.out(Easing.quad) });

  const fam = "'Archivo Black', 'Anton', 'Impact', 'Arial Black', sans-serif";
  const Palavra: React.FC<{ fill: string; blend?: React.CSSProperties["mixBlendMode"] }> =
    ({ fill, blend }) => (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}
           style={{
             position: "absolute", inset: 0, mixBlendMode: blend,
             transform: `translateY(${subida}px)`,
             filter: blur > 0.2 ? `blur(${blur}px)` : undefined,
             opacity: opac,
           }}>
        <text x={width / 2} y={baseline} textAnchor="middle"
              textLength={larguraTexto} lengthAdjust="spacingAndGlyphs"
              fontFamily={fam} fontWeight={900} fontSize={fonte} fill={fill}>
          {palavra}
        </text>
      </svg>
    );

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* reforço de contraste — o bg_nitido do montador já escurece pra 0.62 */}
      <AbsoluteFill style={{
        background: "linear-gradient(180deg, rgba(0,0,0,0.20) 0%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.40) 100%)",
      }} />
      <AbsoluteFill style={{ transform: `scale(${escala})` }}>
        <Palavra fill="rgba(255,255,255,0.85)" blend="overlay" />
        {/* passada fraca em normal: legibilidade mesmo sobre céu estourado */}
        <Palavra fill="rgba(255,255,255,0.12)" />
      </AbsoluteFill>

      {sub ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: height * 0.11 }}>
          <div style={{
            fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
            fontWeight: 600,
            fontSize: height * 0.032,
            letterSpacing: "0.42em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.92)",
            textShadow: "0 2px 18px rgba(0,0,0,0.8)",
            opacity: interpolate(t, [0.9, 1.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            transform: `translateY(${interpolate(t, [0.9, 1.8], [16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)`,
          }}>{sub}</div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

export const TITULO_COMPS: Record<string, React.FC<P>> = { PlaceTitleMassive };
