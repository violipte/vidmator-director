import { AbsoluteFill, interpolate, staticFile, useCurrentFrame } from "remotion";

// Efeitos por CONTEXTO (humor) — estilo documentário premium (VidRush-like).
// Aplicados POR CENA (time-scoped). O humor vem do efeitos.py (Gemini).

// ---- CRT / VHS (scanlines + banda de tracking + vinheta + leve jitter) ----
export const CRTScan: React.FC<{ strength?: number }> = ({ strength = 1 }) => {
  const f = useCurrentFrame();
  const trackY = ((f * 2.5) % 140) / 140 * 110 - 5;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      <AbsoluteFill style={{
        mixBlendMode: "multiply", opacity: 0.4 * strength,
        backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.55) 0px, rgba(0,0,0,0.55) 1.2px, transparent 2.4px, transparent 4.4px)",
      }} />
      <div style={{
        position: "absolute", left: 0, right: 0, top: `${trackY}%`, height: 70, mixBlendMode: "screen",
        background: "linear-gradient(transparent, rgba(180,200,255,0.10), rgba(255,255,255,0.05), transparent)",
      }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 220px 50px rgba(0,0,0,0.62)" }} />
    </AbsoluteFill>
  );
};

// ---- Wash de cor por humor (tinta a tela) ----
export const ColorWash: React.FC<{ color: string; intensity?: number }> = ({ color, intensity = 0.5 }) => {
  const f = useCurrentFrame();
  const pulse = 0.82 + 0.18 * Math.abs(Math.sin(f / 11));
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ backgroundColor: color, mixBlendMode: "color", opacity: Math.min(0.85, intensity) }} />
      <AbsoluteFill style={{ backgroundColor: color, mixBlendMode: "screen", opacity: intensity * 0.32 * pulse }} />
      <AbsoluteFill style={{ backgroundColor: "#000", mixBlendMode: "multiply", opacity: intensity * 0.18,
        maskImage: "radial-gradient(ellipse at center, transparent 35%, black 100%)" }} />
    </AbsoluteFill>
  );
};

// ---- Chiado de TV / static (burst no início da cena, ~8f) ----
export const TVStatic: React.FC<{ durFrames?: number }> = ({ durFrames = 9 }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 2, durFrames - 2, durFrames], [0, 0.85, 0.6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (op <= 0.01) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: op, mixBlendMode: "screen" }}>
      <svg width="100%" height="100%">
        <filter id={`st${f % 5}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 5} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#st${f % 5})`} />
      </svg>
    </AbsoluteFill>
  );
};

// ---- Glitch / flash de impacto (RGB split rápido + flash, ~6f no início) ----
export const GlitchFlash: React.FC<{ durFrames?: number }> = ({ durFrames = 7 }) => {
  const f = useCurrentFrame();
  if (f > durFrames) return null;
  const flash = interpolate(f, [0, 1, 3], [0.55, 0.2, 0], { extrapolateRight: "clamp" });
  const dx = [6, -5, 3, -2, 0][Math.min(4, f)];
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ backgroundColor: "#fff", opacity: flash, mixBlendMode: "screen" }} />
      <AbsoluteFill style={{ backgroundColor: "#ff2d2d", opacity: 0.18, mixBlendMode: "screen", transform: `translateX(${dx}px)` }} />
      <AbsoluteFill style={{ backgroundColor: "#2d6bff", opacity: 0.18, mixBlendMode: "screen", transform: `translateX(${-dx}px)` }} />
    </AbsoluteFill>
  );
};

// ---- Light leak / vazamento de luz (filme antigo): mancha de luz que deriva. screen blend => VISÍVEL em P&B ----
export const LightLeak: React.FC<{ color?: string; intensity?: number }> = ({ color = "#ff8a3c", intensity = 0.5 }) => {
  const f = useCurrentFrame();
  const sx = 50 + 42 * Math.sin(f / 26);
  const sy = 32 + 22 * Math.cos(f / 34);
  const op = Math.min(0.9, (0.42 + 0.58 * Math.abs(Math.sin(f / 38))) * intensity);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: op }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 55% 80% at ${sx}% ${sy}%, ${color}, transparent 58%)` }} />
    </AbsoluteFill>
  );
};

// ---- Film burn / queima de filme: clarão branco-quente rápido (momentos de revelação) ----
export const FilmBurn: React.FC<{ durFrames?: number }> = ({ durFrames = 16 }) => {
  const f = useCurrentFrame();
  if (f > durFrames) return null;
  const op = interpolate(f, [0, 3, 7, durFrames], [0, 0.7, 0.45, 0], { extrapolateRight: "clamp" });
  const s = 1 + 0.15 * (f / durFrames);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: op }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 68% 42%, #fff2d4, #ff8a2c 26%, #b23a00 44%, transparent 62%)", transform: `scale(${s})` }} />
    </AbsoluteFill>
  );
};

// ---- Vinheta de tensão: escurece bordas + leve pulso (funciona em P&B, sem cor) ----
export const TensionVignette: React.FC<{ intensity?: number }> = ({ intensity = 0.5 }) => {
  const f = useCurrentFrame();
  const pulse = 0.8 + 0.2 * Math.abs(Math.sin(f / 9));
  return (
    <AbsoluteFill style={{ pointerEvents: "none",
      boxShadow: `inset 0 0 ${Math.round(220 * intensity)}px ${Math.round(70 * intensity)}px rgba(0,0,0,${(0.7 * pulse).toFixed(3)})` }} />
  );
};

// ---- Receituário: humor -> filtro no vídeo + overlays da cena ----
export type Mood = "tenso" | "frio" | "nostalgia" | "revelacao" | "misterioso" | "neutro";

export const moodVideoFilter = (mood?: string): string => {
  switch (mood) {
    case "nostalgia": return "sepia(0.45) contrast(1.08) saturate(0.72) brightness(1.02)";
    case "tenso": return "contrast(1.12) saturate(1.18)";
    case "frio": return "saturate(0.6) brightness(0.92) contrast(1.05)";
    case "misterioso": return "contrast(1.06) saturate(0.9)";
    default: return "none";
  }
};

// overlays por cena. bw = doc de época P&B -> efeitos de FILME ANTIGO (light leak / film burn / vinheta),
// pois wash de cor não aparece em P&B e CRT/glitch digital é anacrônico. Senão, o estilo VHS/cor.
export const MoodOverlay: React.FC<{ mood?: string; staticIn?: boolean; bw?: boolean }> = ({ mood, staticIn, bw }) => {
  if (bw) {
    return (
      <>
        {mood === "tenso" && <><LightLeak color="#c0331e" intensity={0.5} /><TensionVignette intensity={0.75} /></>}
        {mood === "frio" && <LightLeak color="#3f73b8" intensity={0.42} />}
        {mood === "nostalgia" && <LightLeak color="#ffae5c" intensity={0.6} />}
        {mood === "revelacao" && <FilmBurn />}
        {mood === "misterioso" && <TensionVignette intensity={0.6} />}
      </>
    );
  }
  return (
    <>
      {mood === "nostalgia" && <CRTScan strength={1} />}
      {mood === "misterioso" && <CRTScan strength={0.5} />}
      {mood === "tenso" && <ColorWash color="#c81e1e" intensity={0.5} />}
      {mood === "frio" && <ColorWash color="#2f6bd6" intensity={0.45} />}
      {mood === "revelacao" && <GlitchFlash />}
      {staticIn && <TVStatic />}
    </>
  );
};

// Tratamento de ÉPOCA (doc histórico): grão pesado + vinheta forte + leve flicker. B&W vem no filtro do clipe.
export const PeriodOverlay: React.FC = () => {
  const f = useCurrentFrame();
  const flick = 0.94 + 0.06 * Math.abs(Math.sin(f * 2.3));
  // grão pré-assado (grain.png) animado por background-position — sem feTurbulence em runtime
  const x = (f * 53) % 640;
  const y = (f * 31) % 640;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{
        mixBlendMode: "overlay", opacity: 0.17 * flick,
        backgroundImage: `url(${staticFile("grain.png")})`,
        backgroundRepeat: "repeat", backgroundSize: "560px 560px",
        backgroundPosition: `${x}px ${y}px`,
      }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px 80px rgba(0,0,0,0.72)" }} />
    </AbsoluteFill>
  );
};
