import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// IMAGE CALLOUT — imagem full; CAIXA de callout (accent) com calloutText + LINHA apontando
// p/ o ponto (spotX%,spotY%). A caixa entra com pop; a linha "desenha" até o ponto.
// Container do acervo VidMator (ref.: VidRush "destaque de detalhe"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const ImageCallout: React.FC<{
  image?: string;
  calloutText?: string;
  spotX?: number;
  spotY?: number;
  accent?: string;
}> = ({
  image = "jobs/motos2/clips/moto0.jpg",
  calloutText = "Key detail",
  spotX = 60,
  spotY = 45,
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const imgIn = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const kenScale = interpolate(frame, [0, 150], [1.05, 1.12], { extrapolateRight: "clamp" });
  const spotIn = spring({ frame: frame - 12, fps, config: { damping: 12, stiffness: 140 }, durationInFrames: 16 });
  const lineDraw = interpolate(frame, [22, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const boxIn = spring({ frame: frame - 30, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 18 });
  const pulse = 0.5 + 0.5 * Math.sin(frame / 9);

  const spx = (spotX / 100) * width;
  const spy = (spotY / 100) * height;
  // caixa fica acima/lado oposto do ponto p/ não cobrir
  const boxOnLeft = spotX > 50;
  const boxX = boxOnLeft ? spx - 380 : spx + 380;
  const boxY = spotY > 50 ? spy - 200 : spy + 200;
  const lineEndX = interpolate(lineDraw, [0, 1], [spx, boxX]);
  const lineEndY = interpolate(lineDraw, [0, 1], [spy, boxY]);

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", overflow: "hidden", fontFamily: SANS }}>
      {/* imagem full com leve Ken Burns */}
      <AbsoluteFill style={{ opacity: imgIn }}>
        <Img
          src={staticFile(image)}
          style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kenScale})` }}
        />
      </AbsoluteFill>
      {/* escurecimento leve p/ leitura */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.45) 100%)" }} />

      {/* linha + ponto (SVG) */}
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <line
          x1={spx}
          y1={spy}
          x2={lineEndX}
          y2={lineEndY}
          stroke={accent}
          strokeWidth={3}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${accent})` }}
        />
        {/* ponto pulsante no alvo */}
        <circle cx={spx} cy={spy} r={9} fill={accent} opacity={spotIn} />
        <circle cx={spx} cy={spy} r={9 + pulse * 22} fill="none" stroke={accent} strokeWidth={2} opacity={spotIn * (1 - pulse) * 0.8} />
        <circle cx={spx} cy={spy} r={16} fill="none" stroke="#fff" strokeWidth={2} opacity={spotIn * 0.6} />
      </svg>

      {/* caixa de callout */}
      <div
        style={{
          position: "absolute",
          left: boxX,
          top: boxY,
          transform: `translate(-50%,-50%) scale(${0.6 + 0.4 * boxIn})`,
          opacity: boxIn,
          maxWidth: 460,
          padding: "22px 30px",
          borderRadius: 14,
          background: accent,
          color: "#0a0b0f",
          boxShadow: `0 16px 44px rgba(0,0,0,0.6), 0 0 26px ${accent}55`,
        }}
      >
        <div style={{ fontFamily: DISPLAY, fontSize: 20, letterSpacing: 3, opacity: 0.75, marginBottom: 6 }}>CALLOUT</div>
        <div style={{ fontFamily: DISPLAY, fontSize: 40, lineHeight: 1.12 }}>{calloutText}</div>
      </div>
    </AbsoluteFill>
  );
};
