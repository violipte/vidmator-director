import { AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// PACOTE DE MÁSCARAS DE EDIÇÃO (cinematográfico) — dá assinatura ao footage de stock genérico.
// Camadas: grade fílmica split-tone + halation + névoa + dust + light leak + god rays + grão + vinheta + letterbox.

// --- grade fílmica: sombras teal frias, highlights quentes, leve desaturação (look de LUT) ---
const CinematicGrade: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ mixBlendMode: "multiply", opacity: 0.34, background: "linear-gradient(180deg, #0d2531 0%, #161f29 100%)" }} />
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.13, background: "radial-gradient(circle at 50% 38%, #ffd6a0 0%, transparent 68%)" }} />
    <AbsoluteFill style={{ mixBlendMode: "soft-light", opacity: 0.30, background: "#dcae73" }} />
  </AbsoluteFill>
);

// halation / bloom quente nas luzes
const Halation: React.FC = () => {
  const f = useCurrentFrame();
  const op = 0.10 + 0.04 * Math.abs(Math.sin(f / 40));
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: op, filter: "blur(40px)",
    background: "radial-gradient(circle at 52% 36%, rgba(255,210,150,0.9) 0%, transparent 55%)" }} />;
};

// névoa atmosférica suave (profundidade)
const Haze: React.FC = () => {
  const f = useCurrentFrame();
  const x = 40 + 16 * Math.sin(f / 70);
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: 0.10,
    background: `radial-gradient(ellipse 70% 50% at ${x}% 70%, rgba(220,230,240,0.9) 0%, transparent 60%)` }} />;
};

// dust motes flutuando (screen)
const DUST_N = 55;
const DustMotes: React.FC = () => {
  const f = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const t = f / fps;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none", opacity: 0.5 }}>
      {Array.from({ length: DUST_N }).map((_, i) => {
        const size = random(`dz${i}`) * 3 + 1;
        const op = random(`do${i}`) * 0.5 + 0.2;
        const x = random(`dx${i}`) * width + Math.sin(t * 0.4 + i) * 25;
        const y = height - (((t * (random(`ds${i}`) * 26 + 12)) + i * 57) % (height + 60));
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%",
          background: "#fff4d8", opacity: op, boxShadow: `0 0 ${size * 3}px #fff4d8` }} />;
      })}
    </AbsoluteFill>
  );
};

// light leak quente deriva pela borda
const LightLeakSoft: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const x = 86 + Math.sin(t * 0.3) * 10;
  const op = 0.08 + 0.07 * Math.max(0, Math.sin(t * 0.4));
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen",
    background: `radial-gradient(circle at ${x}% 18%, rgba(255,170,80,${op}) 0%, transparent 44%)` }} />;
};

// god rays diagonais (luz volumétrica falsa)
const GodRays: React.FC = () => {
  const f = useCurrentFrame();
  const op = 0.05 + 0.03 * Math.abs(Math.sin(f / 50));
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: op,
    background: "repeating-linear-gradient(108deg, transparent 0px, rgba(255,225,180,0.5) 2px, transparent 26px)",
    maskImage: "radial-gradient(circle at 75% 8%, black 0%, transparent 60%)",
    WebkitMaskImage: "radial-gradient(circle at 75% 8%, black 0%, transparent 60%)" }} />;
};

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const x = (f * 53) % 600, y = (f * 31) % 600;
  return <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity: 0.08,
    backgroundImage: `url(${staticFile("grain.png")})`, backgroundRepeat: "repeat", backgroundSize: "540px 540px",
    backgroundPosition: `${x}px ${y}px` }} />;
};

const Vignette: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at center, transparent 54%, rgba(0,0,0,0.66) 100%)" }} />
);

const Letterbox: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "6.5%", background: "#000" }} />
    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "6.5%", background: "#000" }} />
  </AbsoluteFill>
);

// pilha completa de máscaras (sobre o footage)
export const EditMaskOverlays: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <CinematicGrade />
    <Haze />
    <Halation />
    <GodRays />
    <LightLeakSoft />
    <DustMotes />
    <Grain />
    <Vignette />
    <Letterbox />
  </AbsoluteFill>
);

// filtro de cor aplicado direto no clipe (parte da grade)
export const MASK_VFILTER = "contrast(1.1) saturate(0.82) brightness(1.03)";

// ---- DEMO antes/depois com divisor deslizante ----
const SAMPLE = "test/mask_sample.jpg";
export const EditMaskDemo: React.FC = () => {
  const f = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  // divisor oscila pra mostrar os dois lados
  const sweep = 50 + 38 * Math.sin((f / durationInFrames) * Math.PI * 2);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", fontFamily: "'Poppins','Segoe UI',sans-serif" }}>
      {/* RAW (fundo) */}
      <Img src={staticFile(SAMPLE)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />

      {/* TRATADO (revela da esquerda até o divisor) */}
      <AbsoluteFill style={{ clipPath: `inset(0 ${(100 - sweep).toFixed(2)}% 0 0)` }}>
        <Img src={staticFile(SAMPLE)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: MASK_VFILTER }} />
        <EditMaskOverlays />
      </AbsoluteFill>

      {/* divisor */}
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${sweep}%`, width: 3, background: "#fff", boxShadow: "0 0 14px rgba(0,0,0,0.7)" }} />
      <div style={{ position: "absolute", top: "50%", left: `${sweep}%`, transform: "translate(-50%,-50%)", width: 46, height: 46, borderRadius: "50%", background: "#fff", boxShadow: "0 2px 10px rgba(0,0,0,0.6)" }} />

      {/* labels */}
      <div style={{ position: "absolute", bottom: 60, left: 60, padding: "10px 22px", borderRadius: 8, background: "rgba(0,0,0,0.55)", color: "#ffce7a", fontSize: 34, fontWeight: 700, letterSpacing: 2 }}>COM MÁSCARAS DE EDIÇÃO</div>
      <div style={{ position: "absolute", top: 60, right: 60, padding: "10px 22px", borderRadius: 8, background: "rgba(0,0,0,0.55)", color: "#cfd6df", fontSize: 34, fontWeight: 700, letterSpacing: 2 }}>STOCK CRU</div>
    </AbsoluteFill>
  );
};
