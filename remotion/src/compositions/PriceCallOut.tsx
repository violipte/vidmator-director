import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// PRICE CALL-OUT — card escuro SOBRE a cena com preço grande (currency+amount, ex "$3,000")
// entrando em ZOOM-OUT + descriptor em caixa-alta embaixo. Container do acervo VidMator.
// Niche-agnostic: priceAmount/currency/descriptorText/accent via props (fundo transparente = overlay).
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const PriceCallOut: React.FC<{
  priceAmount?: number;
  currency?: string;
  descriptorText?: string;
  accent?: string;
}> = ({
  priceAmount = 3000,
  currency = "$",
  descriptorText = "PER SQUARE METRE",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = spring({ frame, fps, config: { damping: 15, stiffness: 95 }, durationInFrames: 22 });
  const scale = interpolate(e, [0, 1], [1.4, 1]);                       // zoom-out na entrada
  const cardOp = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const descOp = interpolate(frame, [16, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 15);
  const amount = priceAmount.toLocaleString("en-US");

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          transform: `scale(${scale})`,
          opacity: cardOp,
          background: "#14161c",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 16,
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          padding: "60px 96px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: DISPLAY,
            fontSize: 200,
            fontWeight: 900,
            color: "#fff",
            lineHeight: 1,
            textShadow: `0 0 ${22 + glow * 26}px ${accent}, 0 0 ${52 + glow * 40}px ${accent}77`,
          }}
        >
          <span style={{ color: accent }}>{currency}</span>
          {amount}
        </div>
        <div
          style={{
            width: 260,
            height: 3,
            margin: "26px auto",
            background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
            boxShadow: `0 0 16px ${accent}`,
            opacity: descOp,
          }}
        />
        <div
          style={{
            fontSize: 40,
            fontWeight: 700,
            letterSpacing: 6,
            color: "#9aa4b2",
            textTransform: "uppercase",
            opacity: descOp,
          }}
        >
          {descriptorText}
        </div>
      </div>
    </AbsoluteFill>
  );
};
