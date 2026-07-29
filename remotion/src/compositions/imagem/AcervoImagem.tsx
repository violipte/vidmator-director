import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO DE IMAGEM — 10 variações (2026-07-20).
   Como uma IMAGEM (ou conjunto) entra em cena. CONTRATO ÚNICO:
   { images: string[], captions?: string[], title?, kicker?, accent? }
   single usa images[0]; duo [0,1]; trio/grid até [3]. Executor
   preenche images com T2/T1 reais (gate) — NUNCA slot vazio.
   ============================================================ */

type P = { images?: string[]; captions?: string[]; title?: string; kicker?: string; accent?: string };
const DISPLAY = F_DISPLAY;
const SERIF = "'Georgia','Times New Roman',serif";
const MONO = F_MONO;
const SANS = F_SANS;
const BG = "#0a0b0f";

/* 01 KEN BURNS CINE — hero: zoom lento + letterbox + vinheta */
export const Img01_KenBurnsCine: React.FC<P> = ({ images = [], title = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = 1.04 + Math.min(f / 800, 0.12);
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})`, opacity: op }} /> : null}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 85% 85% at 50% 50%, transparent 55%, rgba(0,0,0,0.5) 100%)" }} />
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 110, background: "#000" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 110, background: "#000" }} />
      {title ? <div style={{ position: "absolute", bottom: 34, left: 0, right: 0, textAlign: "center", fontFamily: SANS, fontWeight: 700, fontSize: 30, color: "#e8eaee", letterSpacing: 6, opacity: op }}>{title.toUpperCase()}<span style={{ color: accent }}> ▪</span></div> : null}
    </AbsoluteFill>
  );
};

/* 02 POLAROID DROP — polaroid caindo na mesa com rotação + legenda manuscrita */
export const Img02_PolaroidDrop: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 13, stiffness: 110 }, durationInFrames: 24 });
  const rot = interpolate(s, [0, 1], [-14, -4]);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 40%, #2a241d 0%, #17130e 80%)", justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(45deg, rgba(255,255,255,0.015) 0 3px, transparent 3px 7px)" }} />
      <div style={{ background: "#f6f3ea", padding: "26px 26px 90px", borderRadius: 6, transform: `scale(${0.7 + 0.3 * s}) rotate(${rot}deg) translateY(${(1 - s) * -160}px)`, opacity: s, boxShadow: "0 40px 90px rgba(0,0,0,0.65)" }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: 880, height: 620, objectFit: "cover", display: "block" }} /> : null}
        {captions[0] ? <div style={{ position: "absolute", bottom: 22, left: 0, right: 0, textAlign: "center", fontFamily: SERIF, fontStyle: "italic", fontSize: 40, color: "#3a352c" }}>{captions[0]}</div> : null}
      </div>
      <div style={{ position: "absolute", top: 120, left: "50%", transform: "translateX(-50%) rotate(-3deg)", width: 190, height: 54, background: `${accent}33`, border: `1px solid ${accent}55` }} />
    </AbsoluteFill>
  );
};

/* 03 FRAMED GRID PAN — quadro sobre grid escuro com pan lento (assinatura da casa) */
export const Img03_FramedGridPan: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const pan = interpolate(f, [0, 160], [0, -46], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 46%, #0c1120 0%, #05060a 100%)", justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(140,160,220,0.09) 0 1px, transparent 1px 72px), repeating-linear-gradient(90deg, rgba(140,160,220,0.09) 0 1px, transparent 1px 72px)" }} />
      <div style={{ width: "74%", height: "74%", borderRadius: 14, overflow: "hidden", border: "2px solid rgba(150,180,255,0.75)", boxShadow: "0 26px 80px rgba(0,0,0,0.7), 0 0 36px rgba(150,180,255,0.3)", opacity: op }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: "112%", height: "112%", objectFit: "cover", transform: `translateX(${pan}px) scale(1.06)` }} /> : null}
      </div>
      {captions[0] ? <div style={{ position: "absolute", bottom: 52, fontFamily: MONO, fontSize: 27, color: accent, letterSpacing: 4, background: "rgba(0,0,0,0.65)", padding: "9px 26px", borderRadius: 8 }}>{captions[0].toUpperCase()}</div> : null}
    </AbsoluteFill>
  );
};

/* 04 SPLIT SLIDE — duo entrando dos lados com divisor luminoso */
export const Img04_SplitSlide: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 95 }, durationInFrames: 26 });
  const gl = 0.7 + 0.3 * Math.sin(f / 7);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "50%", overflow: "hidden", transform: `translateX(${(1 - s) * -100}%)` }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
        {captions[0] ? <div style={{ position: "absolute", bottom: 44, left: 44, fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>{captions[0]}</div> : null}
      </div>
      <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: "50%", overflow: "hidden", transform: `translateX(${(1 - s) * 100}%)` }}>
        {images[1] ? <Img src={staticFile(images[1])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
        {captions[1] ? <div style={{ position: "absolute", bottom: 44, right: 44, fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>{captions[1]}</div> : null}
      </div>
      <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 6, transform: "translateX(-50%)", background: accent, boxShadow: `0 0 ${26 * gl}px ${accent}`, opacity: s }} />
    </AbsoluteFill>
  );
};

/* 05 BEFORE/AFTER WIPE — cortina deslizando revelando a 2ª imagem */
export const Img05_BeforeAfterWipe: React.FC<P> = ({ images = [], captions = ["Before", "After"], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const wipe = interpolate(f, [16, 76], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000", opacity: op }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", clipPath: `inset(0 ${100 - wipe}% 0 0)` }}>
        {images[1] ? <Img src={staticFile(images[1])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      </div>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${wipe}%`, width: 5, background: accent, boxShadow: `0 0 22px ${accent}` }} />
      <div style={{ position: "absolute", top: 60, left: 70, fontFamily: DISPLAY, fontSize: 40, color: "#fff", background: "rgba(0,0,0,0.6)", padding: "8px 26px", borderRadius: 10, opacity: wipe < 82 ? 1 : 0 }}>{captions[0] ?? "Before"}</div>
      <div style={{ position: "absolute", top: 60, right: 70, fontFamily: DISPLAY, fontSize: 40, color: accent, background: "rgba(0,0,0,0.6)", padding: "8px 26px", borderRadius: 10, opacity: wipe > 30 ? 1 : 0 }}>{captions[1] ?? "After"}</div>
    </AbsoluteFill>
  );
};

/* 06 STACK REVEAL — 3 fotos abrindo em leque (cartas na mesa) */
export const Img06_StackReveal: React.FC<P> = ({ images = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tres = [images[0], images[1] ?? images[0], images[2] ?? images[0]];
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, #14161d 0%, #0a0b0f 78%)", justifyContent: "center", alignItems: "center" }}>
      {tres.map((img, i) => {
        const s = spring({ frame: f - i * 7, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 24 });
        const rot = (i - 1) * 9 * s;
        const dx = (i - 1) * 330 * s;
        return (
          <div key={i} style={{ position: "absolute", transform: `translateX(${dx}px) rotate(${rot}deg) scale(${0.8 + 0.2 * s})`, opacity: s, zIndex: i === 1 ? 3 : 1, boxShadow: "0 34px 80px rgba(0,0,0,0.7)", border: "10px solid #f5f2ea", borderRadius: 8, overflow: "hidden" }}>
            {img ? <Img src={staticFile(img)} style={{ width: 560, height: 700, objectFit: "cover", display: "block" }} /> : null}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* 07 FILMSTRIP SLIDE — tira de filme horizontal deslizando com furos */
export const Img07_FilmstripSlide: React.FC<P> = ({ images = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const x = interpolate(f, [0, 150], [60, -420], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  const quatro = [0, 1, 2, 3].map((i) => images[i % Math.max(1, images.length)]);
  const Furos: React.FC = () => (
    <div style={{ display: "flex", gap: 42, padding: "12px 0" }}>
      {Array.from({ length: 22 }).map((_, i) => <div key={i} style={{ width: 26, height: 34, borderRadius: 5, background: "#0a0b0f", flexShrink: 0 }} />)}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: "#101114", justifyContent: "center", opacity: op }}>
      <div style={{ background: "#1b1c20", transform: `translateX(${x}px) rotate(-2deg)`, boxShadow: "0 30px 80px rgba(0,0,0,0.7)", padding: "6px 0", width: 2600 }}>
        <Furos />
        <div style={{ display: "flex", gap: 18, padding: "0 18px" }}>
          {quatro.map((img, i) => img ? <Img key={i} src={staticFile(img)} style={{ width: 620, height: 400, objectFit: "cover", flexShrink: 0 }} /> : null)}
        </div>
        <Furos />
      </div>
    </AbsoluteFill>
  );
};

/* 08 GRID POP — 2x2 pipocando em sequência com legendas */
export const Img08_GridPop: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const quatro = [0, 1, 2, 3].map((i) => images[i % Math.max(1, images.length)]);
  return (
    <AbsoluteFill style={{ background: "#0c0e12", justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22, width: 1500, height: 860 }}>
        {quatro.map((img, i) => {
          const s = spring({ frame: f - i * 6, fps, config: { damping: 13, stiffness: 130 }, durationInFrames: 20 });
          return (
            <div key={i} style={{ position: "relative", borderRadius: 16, overflow: "hidden", transform: `scale(${0.75 + 0.25 * s})`, opacity: s, border: "1px solid rgba(255,255,255,0.14)", boxShadow: `0 18px 50px rgba(0,0,0,0.55)` }}>
              {img ? <Img src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
              {captions[i] ? <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, background: "linear-gradient(0deg, rgba(0,0,0,0.85) 0%, transparent 100%)", padding: "34px 24px 16px", fontFamily: SANS, fontWeight: 700, fontSize: 28, color: "#fff" }}><span style={{ color: accent, marginRight: 10 }}>▪</span>{captions[i]}</div> : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 09 PAPER TEAR — foto em papel de jornal com fita adesiva + legenda datilografada */
export const Img09_PaperTear: React.FC<P> = ({ images = [], captions = [], kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 26 });
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #15130f 0%, #0d0c09 100%)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", background: "#efe9db", padding: "56px 50px 42px", transform: `rotate(${-2.5 + 1.5 * s}deg) scale(${0.85 + 0.15 * s})`, opacity: s, boxShadow: "0 40px 100px rgba(0,0,0,0.7)" }}>
        <div style={{ position: "absolute", top: -22, left: "50%", transform: "translateX(-50%) rotate(4deg)", width: 220, height: 52, background: "rgba(240,230,190,0.55)", border: "1px solid rgba(0,0,0,0.08)", boxShadow: "0 4px 12px rgba(0,0,0,0.2)" }} />
        {kicker ? <div style={{ fontFamily: MONO, fontSize: 25, color: "#6b6554", letterSpacing: 4, marginBottom: 16 }}>{kicker.toUpperCase()}</div> : null}
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: 980, height: 600, objectFit: "cover", display: "block", filter: "sepia(0.25) contrast(1.05)" }} /> : null}
        {captions[0] ? <div style={{ fontFamily: MONO, fontSize: 30, color: "#4a4437", marginTop: 24, textAlign: "center" }}>{captions[0]}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

/* 10 PARALLAX DEPTH — imagem em profundidade: fundo borrado + frente nítida + texto lateral */
export const Img10_ParallaxDepth: React.FC<P> = ({ images = [], title = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const zBg = 1.15 + Math.min(f / 700, 0.1);
  const zFg = 1.0 + Math.min(f / 1100, 0.06);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zBg})`, filter: "blur(14px) brightness(0.4)" }} /> : null}
      <div style={{ position: "absolute", left: 110, top: "50%", transform: "translateY(-50%)", width: 980, height: 660, borderRadius: 18, overflow: "hidden", boxShadow: `0 40px 100px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.12)`, opacity: op }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zFg})` }} /> : null}
      </div>
      <div style={{ position: "absolute", right: 120, top: "50%", transform: "translateY(-50%)", maxWidth: 560, opacity: op }}>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 7, marginBottom: 20 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 62, color: "#fff", lineHeight: 1.2, textShadow: "0 6px 26px rgba(0,0,0,0.8)" }}>{title}</div>
        <div style={{ width: 120, height: 5, background: accent, borderRadius: 3, marginTop: 26, boxShadow: `0 0 16px ${accent}99` }} />
      </div>
    </AbsoluteFill>
  );
};

/* 11 VINTAGE ANGLED — P&B/sépia angulada com zoom (registro histórico) */
export const Img11_VintageAngled: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 150], [1.28, 1.08], { extrapolateRight: "clamp" });
  const rot = interpolate(f, [0, 150], [-16, -5], { extrapolateRight: "clamp" });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ position: "absolute", width: "118%", height: "118%", left: "-9%", top: "-9%", objectFit: "cover", transform: `scale(${s}) rotate(${rot}deg)`, filter: "grayscale(1) sepia(0.22) contrast(1.1) brightness(0.88)", opacity: op }} /> : null}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 80% at 50% 50%, transparent 42%, rgba(0,0,0,0.78) 100%)" }} />
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 2px, transparent 2px 4px)", opacity: 0.5 }} />
      {captions[0] ? <div style={{ position: "absolute", bottom: 64, left: 0, right: 0, textAlign: "center", fontFamily: MONO, fontSize: 30, color: "#e8e2d4", letterSpacing: 5, textShadow: "0 3px 14px rgba(0,0,0,0.9)" }}>{captions[0].toUpperCase()}</div> : null}
    </AbsoluteFill>
  );
};

/* 12 SPOTLIGHT DETAIL — escuro com holofote circular indo até o detalhe + label */
export const Img12_SpotlightDetail: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const cx = interpolate(f, [15, 60], [50, 66], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const cy = interpolate(f, [15, 60], [50, 42], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const r = interpolate(f, [15, 60], [42, 15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lblOp = interpolate(f, [62, 76], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      <AbsoluteFill style={{ background: `radial-gradient(circle ${r}% at ${cx}% ${cy}%, transparent 0%, transparent 60%, rgba(0,0,0,0.88) 100%)` }} />
      {captions[0] ? <div style={{ position: "absolute", left: `${cx}%`, top: `${cy + r * 0.75}%`, transform: "translateX(-50%)", fontFamily: SANS, fontWeight: 800, fontSize: 32, color: "#fff", background: "rgba(0,0,0,0.7)", border: `2px solid ${accent}`, padding: "10px 26px", borderRadius: 10, opacity: lblOp }}>{captions[0]}</div> : null}
    </AbsoluteFill>
  );
};

/* 13 MAGNIFIER INSPECT — lupa deslizando sobre a foto ampliando o trecho */
export const Img13_MagnifierInspect: React.FC<P> = ({ images = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const mx = interpolate(f, [10, 140], [28, 70], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  const my = interpolate(f, [10, 140], [60, 38], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const R = 190;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.62)" }} /> : null}
      <div style={{ position: "absolute", left: `calc(${mx}% - ${R}px)`, top: `calc(${my}% - ${R}px)`, width: R * 2, height: R * 2, borderRadius: "50%", overflow: "hidden", border: `7px solid ${accent}`, boxShadow: `0 0 44px ${accent}55, 0 24px 60px rgba(0,0,0,0.7)`, opacity: op }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ position: "absolute", width: "1920px", height: "1080px", objectFit: "cover", left: `${-(mx / 100) * 1920 * 1.7 + R}px`, top: `${-(my / 100) * 1080 * 1.7 + R}px`, transform: "scale(1.7)", transformOrigin: "top left" }} /> : null}
      </div>
      <div style={{ position: "absolute", left: `calc(${mx}% + ${R * 0.62}px)`, top: `calc(${my}% + ${R * 0.62}px)`, width: 14, height: 150, background: `linear-gradient(${accent}, #7a5410)`, borderRadius: 8, transform: "rotate(-45deg)", transformOrigin: "top center", opacity: op }} />
    </AbsoluteFill>
  );
};

/* 14 TITLE CUTOUT — título GIGANTE com a imagem aparecendo DENTRO das letras */
export const Img14_TitleCutout: React.FC<P> = ({ images = [], title = "", accent = "#f59e0b" }) => {
  // REGRA DE FERRO pós-QA 21/07: sem título REAL não renderiza (o default "HILUX" vazou num vídeo de Harley)
  if (!title || !images[0]) return null;
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const s = 1.0 + Math.min(f / 900, 0.08);
  return (
    <AbsoluteFill style={{ background: "#0c0d10", justifyContent: "center", alignItems: "center" }}>
      <div style={{
        fontFamily: DISPLAY, fontSize: 300, lineHeight: 1, textAlign: "center", opacity: op,
        backgroundImage: images[0] ? `url(${staticFile(images[0])})` : "none",
        backgroundSize: "cover", backgroundPosition: "center",
        WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent",
        transform: `scale(${s})`, letterSpacing: 4,
        textShadow: "none", filter: `drop-shadow(0 20px 60px rgba(0,0,0,0.8))`,
      }}>{title.toUpperCase()}</div>
      <div style={{ width: 200, height: 6, background: accent, borderRadius: 3, marginTop: 40, boxShadow: `0 0 22px ${accent}`, opacity: op }} />
    </AbsoluteFill>
  );
};

/* 15 CORK BOARD — mural de detetive: 2 fotos pinadas + barbante ligando */
export const Img15_CorkBoardPin: React.FC<P> = ({ images = [], captions = [], accent = "#e23c3c" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s1 = spring({ frame: f, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 20 });
  const s2 = spring({ frame: f - 10, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 20 });
  const fio = interpolate(f, [26, 58], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const Pin: React.FC<{ c: string }> = ({ c }) => <div style={{ position: "absolute", top: -16, left: "50%", transform: "translateX(-50%)", width: 34, height: 34, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, ${c}, #7a1f1f)`, boxShadow: "0 6px 14px rgba(0,0,0,0.6)", zIndex: 5 }} />;
  return (
    <AbsoluteFill style={{ background: "repeating-linear-gradient(35deg, #8a6a48 0 3px, #7d5f40 3px 6px)", justifyContent: "center" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, transparent 40%, rgba(40,25,12,0.65) 100%)" }} />
      <div style={{ position: "absolute", left: 200, top: 200, transform: `rotate(-5deg) scale(${0.8 + 0.2 * s1})`, opacity: s1, background: "#f3efe4", padding: "16px 16px 54px", boxShadow: "0 24px 60px rgba(0,0,0,0.5)" }}>
        <Pin c="#e23c3c" />
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: 560, height: 400, objectFit: "cover", display: "block" }} /> : null}
        {captions[0] ? <div style={{ fontFamily: MONO, fontSize: 26, color: "#3c352a", textAlign: "center", marginTop: 14 }}>{captions[0]}</div> : null}
      </div>
      <div style={{ position: "absolute", right: 210, top: 330, transform: `rotate(4deg) scale(${0.8 + 0.2 * s2})`, opacity: s2, background: "#f3efe4", padding: "16px 16px 54px", boxShadow: "0 24px 60px rgba(0,0,0,0.5)" }}>
        <Pin c="#3c6ee2" />
        {images[1] ? <Img src={staticFile(images[1])} style={{ width: 560, height: 400, objectFit: "cover", display: "block" }} /> : null}
        {captions[1] ? <div style={{ fontFamily: MONO, fontSize: 26, color: "#3c352a", textAlign: "center", marginTop: 14 }}>{captions[1]}</div> : null}
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
        <path d="M 500 215 Q 960 560 1400 350" fill="none" stroke={accent} strokeWidth={7} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - fio} style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.5))" }} />
      </svg>
    </AbsoluteFill>
  );
};

/* 16 ZOOM OUT REVEAL — começa no detalhe fechado e abre revelando a cena toda */
export const Img16_ZoomOutReveal: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 110], [3.1, 1.02], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const capOp = interpolate(f, [96, 116], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})`, transformOrigin: "62% 38%" }} /> : null}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 88% 88% at 50% 50%, transparent 56%, rgba(0,0,0,0.46) 100%)" }} />
      {captions[0] ? <div style={{ position: "absolute", bottom: 70, left: 0, right: 0, textAlign: "center", fontFamily: DISPLAY, fontSize: 52, color: "#fff", textShadow: "0 6px 26px rgba(0,0,0,0.9)", opacity: capOp }}>{captions[0]}<span style={{ color: accent }}>.</span></div> : null}
    </AbsoluteFill>
  );
};

/* 17 DIAGONAL DUO — duas imagens divididas por diagonal deslizante */
export const Img17_DiagonalDuo: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 28 });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <div style={{ position: "absolute", inset: 0, clipPath: "polygon(0 0, 62% 0, 38% 100%, 0 100%)", transform: `translateX(${(1 - s) * -70}%)` }}>
        {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      </div>
      <div style={{ position: "absolute", inset: 0, clipPath: "polygon(62% 0, 100% 0, 100% 100%, 38% 100%)", transform: `translateX(${(1 - s) * 70}%)` }}>
        {images[1] ? <Img src={staticFile(images[1])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      </div>
      <div style={{ position: "absolute", left: "50%", top: "50%", width: 8, height: "150%", background: accent, transform: `translate(-50%,-50%) rotate(13.5deg) scaleY(${s})`, boxShadow: `0 0 30px ${accent}` }} />
      {captions[0] ? <div style={{ position: "absolute", bottom: 52, left: 64, fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.95)", opacity: s }}>{captions[0]}</div> : null}
      {captions[1] ? <div style={{ position: "absolute", top: 52, right: 64, fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.95)", opacity: s }}>{captions[1]}</div> : null}
    </AbsoluteFill>
  );
};

/* 18 PHOTO STAT BADGE — foto + placa lateral com número grande + label */
export const Img18_PhotoStatBadge: React.FC<P> = ({ images = [], title = "", kicker = "", captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - 8, fps, config: { damping: 14, stiffness: 110 }, durationInFrames: 24 });
  const z = 1.02 + Math.min(f / 1000, 0.07);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {images[0] ? <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, filter: "brightness(0.72)" }} /> : null}
      {/* 29/07 (print Piter): badge SÓ com conteúdo — title vazio deixava um risco
          âmbar órfão flutuando sobre a foto */}
      {(title || kicker || captions[0]) ? (
        <>
          <AbsoluteFill style={{ background: "linear-gradient(70deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.25) 42%, transparent 65%)" }} />
          <div style={{ position: "absolute", left: 110, top: "50%", transform: `translateY(-50%) translateX(${(1 - s) * -80}px)`, opacity: s }}>
            {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 7, marginBottom: 16 }}>{kicker.toUpperCase()}</div> : null}
            <div style={{ fontFamily: DISPLAY, fontSize: 170, color: "#fff", lineHeight: 1, textShadow: `0 0 54px ${accent}55` }}>{title}</div>
            {captions[0] ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 32, color: "#dfe2e8", marginTop: 18, maxWidth: 620 }}>{captions[0]}</div> : null}
            <div style={{ width: 140, height: 6, background: accent, borderRadius: 3, marginTop: 26, boxShadow: `0 0 18px ${accent}` }} />
          </div>
        </>
      ) : null}
    </AbsoluteFill>
  );
};

/* 19 NEWS CLIPPING — recorte de jornal: cabeçalho + foto + frase grifada */
export const Img19_NewsClipping: React.FC<P> = ({ images = [], captions = [], title = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 95 }, durationInFrames: 26 });
  const grifo = interpolate(f, [40, 72], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #14120e 0%, #0c0b08 100%)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ background: "#f2edE0".toLowerCase(), width: 1180, padding: "44px 56px 40px", transform: `rotate(${-1.5 + 1 * s}deg) scale(${0.88 + 0.12 * s})`, opacity: s, boxShadow: "0 46px 110px rgba(0,0,0,0.75)" }}>
        <div style={{ borderBottom: "3px solid #26221a", paddingBottom: 12, marginBottom: 18, display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <span style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 34, color: "#26221a", letterSpacing: 2 }}>{(kicker || "THE DAILY HERALD").toUpperCase()}</span>
          <span style={{ fontFamily: MONO, fontSize: 20, color: "#6b6350" }}>EDITION 4,218</span>
        </div>
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 56, color: "#191510", lineHeight: 1.12, marginBottom: 22 }}>{title}</div>
        <div style={{ display: "flex", gap: 30 }}>
          {images[0] ? <Img src={staticFile(images[0])} style={{ width: 520, height: 340, objectFit: "cover", filter: "grayscale(0.85) contrast(1.05)" }} /> : null}
          <div style={{ flex: 1 }}>
            <span style={{
              fontFamily: SERIF, fontSize: 29, lineHeight: 1.5, color: "#26221a",
              backgroundImage: `linear-gradient(${accent}59, ${accent}59)`, backgroundRepeat: "no-repeat",
              backgroundSize: `${grifo}% 42%`, backgroundPosition: "0 82%",
            }}>{captions[0] ?? ""}</span>
            {/* R-32: corpo era LOREM HARDCODED da era Hilux e VAZOU legível num vídeo de tênis.
                Sem texto real (captions[1]) => sem corpo — nunca texto de exemplo. */}
            {captions[1] ? <div style={{ fontFamily: SERIF, fontSize: 24, lineHeight: 1.55, color: "#4a4437", marginTop: 14, columnCount: 1 }}>
              {captions[1]}
            </div> : null}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 20 TRIPLE CAROUSEL — 3 imagens em carrossel, a central em foco */
export const Img20_TripleCarousel: React.FC<P> = ({ images = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tres = [images[0], images[1] ?? images[0], images[2] ?? images[0]];
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 45%, #12141b 0%, #0a0b0f 80%)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", gap: 46, alignItems: "center" }}>
        {tres.map((img, i) => {
          const centro = i === 1;
          const s = spring({ frame: f - i * 6, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 24 });
          return (
            <div key={i} style={{ position: "relative", borderRadius: 18, overflow: "hidden", opacity: s,
              transform: `scale(${(centro ? 1 : 0.82) * (0.8 + 0.2 * s)}) translateY(${(1 - s) * 60}px)`,
              border: centro ? `3px solid ${accent}` : "1px solid rgba(255,255,255,0.15)",
              boxShadow: centro ? `0 30px 80px rgba(0,0,0,0.7), 0 0 44px ${accent}44` : "0 20px 50px rgba(0,0,0,0.6)",
              filter: centro ? "none" : "brightness(0.55)" }}>
              {img ? <Img src={staticFile(img)} style={{ width: centro ? 760 : 520, height: centro ? 560 : 420, objectFit: "cover", display: "block" }} /> : null}
              {centro && captions[0] ? <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, background: "linear-gradient(0deg, rgba(0,0,0,0.88) 0%, transparent 100%)", padding: "40px 26px 18px", fontFamily: SANS, fontWeight: 800, fontSize: 30, color: "#fff" }}>{captions[0]}</div> : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ============ VIDRUSH PACK (decupagem 14 vídeos, 24/07) ============ */

/* 21 PRODUCT ANNOUNCE — foto do produto full + rank+nome condensed POR CIMA (kicker=apelido).
   Ref.: '#8 KASTKING CENTRON: BACKUP WORKHORSE' — anúncio nunca é texto sem produto. */
export const Img21_ProductAnnounce: React.FC<P> = ({ images = [], title = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 14, stiffness: 95 }, durationInFrames: 22 });
  const zoom = 1.04 + Math.min(f / 1200, 0.06);
  if (!images[0] || !title) return null;
  return (
    <AbsoluteFill style={{ background: BG }}>
      <Img src={staticFile(images[0])} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})` }} />
      <AbsoluteFill style={{ background: "linear-gradient(10deg, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.30) 38%, transparent 62%)" }} />
      <div style={{ position: "absolute", left: 90, bottom: 84, opacity: s, transform: `translateY(${(1 - s) * 34}px)` }}>
        <div style={{ width: interpolate(s, [0, 1], [0, 130]), height: 6, background: accent, marginBottom: 18, boxShadow: `0 0 20px ${accent}` }} />
        <div style={{ fontFamily: DISPLAY, fontSize: 96, color: "#fff", lineHeight: 1.02, maxWidth: 1300,
          textTransform: "uppercase", letterSpacing: 1, textShadow: "0 8px 40px rgba(0,0,0,0.9)" }}>{title}</div>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, color: accent, letterSpacing: 6, marginTop: 12, textTransform: "uppercase", textShadow: "0 4px 20px rgba(0,0,0,0.9)" }}>{kicker}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

/* 22 PRODUCT CALLOUTS — imagem central + 2-4 labels com linha (captions=labels). */
export const Img22_ProductCallouts: React.FC<P> = ({ images = [], captions = [], title = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const labs = captions.filter(Boolean).slice(0, 4);
  if (!images[0] || labs.length < 2) return null;
  const POS = [{ x: 6, y: 22, ax: "left" }, { x: 94, y: 30, ax: "right" }, { x: 6, y: 68, ax: "left" }, { x: 94, y: 74, ax: "right" }];
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 90% 90% at 50% 46%, #101318 0%, ${BG} 82%)` }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(150,170,210,0.07) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(150,170,210,0.07) 0 1px, transparent 1px 64px)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <Img src={staticFile(images[0])} style={{ maxWidth: "58%", maxHeight: "72%", objectFit: "contain", filter: "drop-shadow(0 30px 70px rgba(0,0,0,0.75))" }} />
      </AbsoluteFill>
      {title ? <div style={{ position: "absolute", top: 56, width: "100%", textAlign: "center", fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#e8e4da", letterSpacing: 7, textTransform: "uppercase" }}>{title}</div> : null}
      {labs.map((c, i) => {
        const p = POS[i];
        const op = interpolate(f, [8 + i * 7, 22 + i * 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <div key={i} style={{ position: "absolute", left: `${p.x}%`, top: `${p.y}%`, transform: p.ax === "right" ? "translateX(-100%)" : undefined, opacity: op }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexDirection: p.ax === "right" ? "row-reverse" : "row" }}>
              <div style={{ background: "rgba(10,11,15,0.85)", border: `1.5px solid ${accent}99`, padding: "10px 22px", borderRadius: 8, fontFamily: SANS, fontWeight: 700, fontSize: 26, color: "#f2efe6", whiteSpace: "nowrap" }}>{c}</div>
              <div style={{ width: 90, height: 2, background: `linear-gradient(${p.ax === "right" ? "270deg" : "90deg"}, ${accent}, transparent)` }} />
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* 23 COLLAGE COMPARE — 2-3 polaroids com labels sobre fundo texturizado (captions=labels). */
export const Img23_CollageCompare: React.FC<P> = ({ images = [], captions = [], title = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const im = images.filter(Boolean).slice(0, 3);
  if (im.length < 2) return null;
  const ROT = [-3.2, 2.4, -1.6];
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #14110c 0%, #0b0a07 100%)", alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(220,205,170,0.05) 0 1px, transparent 1px 46px), repeating-linear-gradient(90deg, rgba(220,205,170,0.05) 0 1px, transparent 1px 46px)" }} />
      {title ? <div style={{ position: "absolute", top: 62, fontFamily: DISPLAY, fontSize: 46, color: "#efe9da", letterSpacing: 2 }}>{title}</div> : null}
      <div style={{ display: "flex", gap: 70, alignItems: "center" }}>
        {im.map((src, i) => {
          const s = spring({ frame: Math.max(0, f - i * 7), fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 24 });
          return (
            <div key={i} style={{ background: "#f5f1e6", padding: "16px 16px 60px 16px", borderRadius: 4,
              transform: `rotate(${ROT[i]}deg) translateY(${(1 - s) * 60}px)`, opacity: s,
              boxShadow: "0 30px 70px rgba(0,0,0,0.65)" }}>
              <Img src={staticFile(src)} style={{ width: im.length === 2 ? 560 : 430, height: im.length === 2 ? 400 : 330, objectFit: "cover" }} />
              {captions[i] ? <div style={{ position: "absolute", left: "50%", bottom: 14, transform: "translateX(-50%)",
                background: accent, color: "#111", fontFamily: SANS, fontWeight: 800, fontSize: 23,
                padding: "5px 18px", borderRadius: 4, whiteSpace: "nowrap", letterSpacing: 1 }}>{captions[i].toUpperCase()}</div> : null}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO ---------------- */
export const IMAGEM_MANIFEST = [
  { id: 0, comp: "Img01_KenBurnsCine", imgs: 1, quando: "hero/cena principal — foto forte com letterbox" },
  { id: 1, comp: "Img02_PolaroidDrop", imgs: 1, quando: "memória/registro histórico casual" },
  { id: 2, comp: "Img03_FramedGridPan", imgs: 1, quando: "foto no quadro técnico da casa (assinatura)" },
  { id: 3, comp: "Img04_SplitSlide", imgs: 2, quando: "dois lados/rivais/paralelo (com legendas)" },
  { id: 4, comp: "Img05_BeforeAfterWipe", imgs: 2, quando: "antes/depois com cortina deslizante" },
  { id: 5, comp: "Img06_StackReveal", imgs: 3, quando: "conjunto de evidências/registros em leque" },
  { id: 6, comp: "Img07_FilmstripSlide", imgs: 4, quando: "sequência de época/arquivo (tira de filme)" },
  { id: 7, comp: "Img08_GridPop", imgs: 4, quando: "4 itens/aspectos com legendas (grid vivo)" },
  { id: 8, comp: "Img09_PaperTear", imgs: 1, quando: "documento/jornal/dossiê (papel + fita)" },
  { id: 9, comp: "Img10_ParallaxDepth", imgs: 1, quando: "foto + texto lateral (profundidade premium)" },
  { id: 10, comp: "Img11_VintageAngled", imgs: 1, quando: "registro HISTÓRICO — P&B angulada com grão" },
  { id: 11, comp: "Img12_SpotlightDetail", imgs: 1, quando: "dirigir o olhar a um DETALHE (holofote + label)" },
  { id: 12, comp: "Img13_MagnifierInspect", imgs: 1, vetado: true, quando: "VETADA pelo Piter 20/07 ('lupa zuada') — NÃO usar" },
  { id: 13, comp: "Img14_TitleCutout", imgs: 1, quando: "título GIGANTE com a foto dentro das letras (hook)" },
  { id: 14, comp: "Img15_CorkBoardPin", imgs: 2, quando: "mural de detetive: 2 fotos pinadas + barbante" },
  { id: 15, comp: "Img16_ZoomOutReveal", imgs: 1, quando: "revelação: abre do detalhe pra cena inteira" },
  { id: 16, comp: "Img17_DiagonalDuo", imgs: 2, quando: "dois mundos divididos na diagonal" },
  { id: 17, comp: "Img18_PhotoStatBadge", imgs: 1, quando: "foto + NÚMERO grande lateral (title=stat)" },
  { id: 18, comp: "Img19_NewsClipping", imgs: 1, quando: "recorte de jornal com frase grifada" },
  { id: 19, comp: "Img20_TripleCarousel", imgs: 3, quando: "carrossel de 3, central em foco" },
  { id: 20, comp: "Img21_ProductAnnounce", imgs: 1, quando: "ANÚNCIO: foto do produto + rank+nome por cima (R-111)" },
  { id: 21, comp: "Img22_ProductCallouts", imgs: 1, quando: "specs: produto central + 2-4 callouts com linha" },
  { id: 22, comp: "Img23_CollageCompare", imgs: 2, quando: "comparação: 2-3 polaroids com labels" },
];

export const IMAGEM_COMPS: Record<string, React.FC<P>> = {
  Img01_KenBurnsCine, Img02_PolaroidDrop, Img03_FramedGridPan, Img04_SplitSlide, Img05_BeforeAfterWipe,
  Img06_StackReveal, Img07_FilmstripSlide, Img08_GridPop, Img09_PaperTear, Img10_ParallaxDepth,
  Img11_VintageAngled, Img12_SpotlightDetail, Img13_MagnifierInspect, Img14_TitleCutout, Img15_CorkBoardPin,
  Img16_ZoomOutReveal, Img17_DiagonalDuo, Img18_PhotoStatBadge, Img19_NewsClipping, Img20_TripleCarousel,
  Img21_ProductAnnounce, Img22_ProductCallouts, Img23_CollageCompare,
};
