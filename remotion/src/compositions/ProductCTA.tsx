import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// CTA DE PRODUTO (faceless): fundo de pessoas se exercitando + foto do produto (grande, à esquerda) +
// oferta por tempo limitado (link no 1º comentário fixado) + QR code. Parametrizado por canal.

type Props = {
  bg?: string;            // footage/imagem de fundo
  productImg?: string;    // PNG do produto (transparente -> flutua, sem moldura)
  qrImg?: string;         // QR (gerado do link, ou enviado)
  headline?: string;
  offer?: string;
};

export const ProductCTA: React.FC<Props> = ({
  bg = "test/cta_bg.jpg",
  productImg = "cta/produto.png",
  qrImg = "cta/qr.png",
  headline = "RELEASE WHAT YOUR HIPS ARE HOLDING",
  offer = "LINK IN THE FIRST PINNED COMMENT",
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inL = spring({ frame: f, fps, config: { damping: 18 }, durationInFrames: 24 });
  const inR = spring({ frame: f - 8, fps, config: { damping: 18 }, durationInFrames: 24 });
  const headIn = interpolate(f, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const float = Math.sin(f / 26) * 8;                 // produto flutua leve
  const qrPulse = 1 + 0.03 * Math.sin(f / 8);
  const arrowDy = 8 * Math.abs(Math.sin(f / 11));
  const GREEN = "#39ff14";

  return (
    <AbsoluteFill style={{ fontFamily: "'Poppins','Segoe UI',sans-serif", overflow: "hidden" }}>
      {/* fundo: pessoas se exercitando, escurecido p/ legibilidade */}
      <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.46) saturate(0.85) contrast(1.05)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(5,8,12,0.9) 0%, rgba(5,8,12,0.45) 58%, rgba(5,8,12,0.78) 100%)" }} />

      {/* headline (topo, menor) */}
      <div style={{ position: "absolute", top: 50, width: "100%", textAlign: "center", opacity: headIn }}>
        <div style={{ display: "inline-block", color: "#fff", fontSize: 46, fontWeight: 800, letterSpacing: 1, textShadow: "0 4px 16px rgba(0,0,0,0.75)" }}>{headline}</div>
      </div>

      {/* PRODUTO (grande, flutuando, sem moldura) */}
      <Img src={staticFile(productImg)} style={{
        position: "absolute", left: 70, top: 190, width: 740, height: 560, objectFit: "contain",
        transform: `translateX(${(1 - inL) * -90}px) translateY(${float}px)`, opacity: inL,
        filter: "drop-shadow(0 22px 44px rgba(0,0,0,0.65)) drop-shadow(0 0 30px rgba(255,150,40,0.28))",
      }} />

      {/* oferta (esquerda-baixo, texto menor) */}
      <div style={{ position: "absolute", left: 96, top: 792, opacity: inL }}>
        <div style={{ display: "inline-block", padding: "6px 18px", borderRadius: 7, background: "#e23b3b", color: "#fff", fontSize: 26, fontWeight: 800, letterSpacing: 2, boxShadow: "0 0 18px rgba(226,59,59,0.6)" }}>⏳ LIMITED TIME</div>
        <div style={{ marginTop: 16, color: "#fff", fontSize: 30, fontWeight: 700, lineHeight: 1.25 }}>{offer}</div>
        <div style={{ marginTop: 4, fontSize: 52, color: GREEN, transform: `translateY(${arrowDy}px)`, textShadow: `0 0 16px ${GREEN}` }}>↓</div>
      </div>

      {/* QR (direita, menor) */}
      <div style={{ position: "absolute", right: 180, top: "50%", transform: `translateY(-50%) translateX(${(1 - inR) * 90}px) scale(${qrPulse})`, opacity: inR, textAlign: "center" }}>
        <div style={{ padding: 20, borderRadius: 18, background: "#fff", boxShadow: "0 12px 34px rgba(0,0,0,0.6)" }}>
          <Img src={staticFile(qrImg)} style={{ width: 250, height: 250, display: "block" }} />
        </div>
        <div style={{ marginTop: 14, color: "#fff", fontSize: 28, fontWeight: 800, letterSpacing: 3, textShadow: "0 3px 10px rgba(0,0,0,0.7)" }}>SCAN TO GET IT</div>
      </div>
    </AbsoluteFill>
  );
};

export const ProductCTAMock: React.FC = () => <ProductCTA />;
