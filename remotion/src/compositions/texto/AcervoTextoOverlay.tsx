import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO TEXTO-OVERLAY — 10 variações TRANSPARENTES (2026-07-20).
   Entram POR CIMA de footage. Contrato único: { text, kicker?, accent? }.
   Todas têm PROTEÇÃO DE CONTRASTE local (scrim/placa) — legíveis sobre
   qualquer clipe. Ref.: decupagem VidRush (chapter sobre footage, caption
   box, date pill, callout central, atribuição de citação).
   ============================================================ */

type P = { text?: string; kicker?: string; accent?: string };
const DISPLAY = F_DISPLAY;
const SERIF = "'Georgia','Times New Roman',serif";
const MONO = F_MONO;
const SANS = F_SANS;

/* 01 CHAPTER BIG — abertura de capítulo: kicker mono + título display, canto inf-esq, scrim de canto */
export const Ovl01_ChapterBig: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 24 });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(50deg, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.35) 34%, transparent 62%)" }} />
      <div style={{ position: "absolute", left: 90, bottom: 90, opacity: s, transform: `translateY(${(1 - s) * 40}px)` }}>
        {kicker ? <div style={{ fontFamily: MONO, fontSize: 30, color: accent, letterSpacing: 8, marginBottom: 14 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ width: interpolate(s, [0, 1], [0, 150]), height: 5, background: accent, borderRadius: 3, marginBottom: 20, boxShadow: `0 0 18px ${accent}aa` }} />
        <div style={{ fontFamily: DISPLAY, fontSize: 88, color: "#fff", lineHeight: 1.12, maxWidth: 1150, textShadow: "0 6px 30px rgba(0,0,0,0.85)" }}>{text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 02 SUBCHAPTER LINE — subtítulo discreto topo-esq: linha + texto médio, faixa sutil */
export const Ovl02_SubchapterLine: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 18], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: 96, display: "flex", alignItems: "center", gap: 26, opacity: s, transform: `translateX(${(1 - s) * -60}px)` }}>
        <div style={{ width: 10, height: 84, background: accent, boxShadow: `0 0 20px ${accent}99` }} />
        <div style={{ background: "rgba(0,0,0,0.62)", backdropFilter: "blur(3px)", padding: "18px 40px 18px 24px", borderRadius: "0 12px 12px 0" }}>
          {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 21, color: accent, letterSpacing: 6, marginBottom: 6 }}>{kicker.toUpperCase()}</div> : null}
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 44, color: "#fff" }}>{text}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 03 LOWER THIRD — clássico: placa translúcida deslizando com barra accent (nome/rótulo) */
export const Ovl03_LowerThird: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 110 }, durationInFrames: 22 });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 90, bottom: 110, overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "stretch", transform: `translateX(${(1 - s) * -105}%)` }}>
          <div style={{ width: 9, background: accent, boxShadow: `0 0 16px ${accent}` }} />
          <div style={{ background: "rgba(8,9,12,0.78)", backdropFilter: "blur(4px)", padding: "16px 44px 16px 26px", borderRadius: "0 10px 10px 0" }}>
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 40, color: "#fff" }}>{text}</div>
            {kicker ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 22, color: accent, letterSpacing: 3, marginTop: 4 }}>{kicker}</div> : null}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 04 FOOTNOTE PILL — nota de rodapé/fonte: pill pequena base-centro com asterisco */
export const Ovl04_FootnotePill: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
      <div style={{ marginBottom: 64, display: "flex", alignItems: "center", gap: 14, background: "rgba(0,0,0,0.68)", backdropFilter: "blur(4px)", padding: "12px 30px", borderRadius: 999, border: "1px solid rgba(255,255,255,0.12)", opacity: op, transform: `translateY(${(1 - op) * 18}px)` }}>
        <span style={{ fontFamily: SERIF, fontSize: 30, color: accent, lineHeight: 1 }}>*</span>
        <span style={{ fontFamily: SANS, fontSize: 25, color: "#d9dbe0" }}>
          {kicker ? <b style={{ color: "#fff", marginRight: 8 }}>{kicker}:</b> : null}{text}
        </span>
      </div>
    </AbsoluteFill>
  );
};

/* 05 CORNER TAG — tag de arquivo canto sup-dir: mono com colchetes, piscada de REC */
export const Ovl05_CornerTag: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const dot = Math.floor(f / 18) % 2 === 0;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", right: 84, top: 78, textAlign: "right", opacity: op }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "rgba(0,0,0,0.6)", padding: "10px 22px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.14)" }}>
          <span style={{ width: 12, height: 12, borderRadius: "50%", background: accent, opacity: dot ? 1 : 0.25, boxShadow: `0 0 10px ${accent}` }} />
          <span style={{ fontFamily: MONO, fontSize: 26, color: "#eceef2", letterSpacing: 3 }}>{(kicker ? kicker.toUpperCase() + " · " : "") + text}</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 06 CENTER PUNCH — palavra/frase curta central com scrim radial (impacto protegido) */
export const Ovl06_CenterPunch: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 12, stiffness: 150 }, durationInFrames: 18 });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 46% 34% at 50% 50%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.3) 55%, transparent 78%)" }} />
      <div style={{ textAlign: "center", opacity: s, transform: `scale(${0.6 + 0.4 * s})` }}>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 9, marginBottom: 16 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 110, color: "#fff", lineHeight: 1.1, maxWidth: 1300, textShadow: `0 0 44px ${accent}55, 0 8px 34px rgba(0,0,0,0.9)` }}>{text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 07 QUOTE ATTRIBUTION — aspas grandes + frase + autor, baixo-esq sobre footage */
export const Ovl07_QuoteAttribution: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(0deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.28) 36%, transparent 60%)" }} />
      <div style={{ position: "absolute", left: 110, bottom: 100, maxWidth: 1250, opacity: op, transform: `translateY(${(1 - op) * 26}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 120, color: accent, lineHeight: 0.6, marginBottom: 8, textShadow: `0 0 26px ${accent}55` }}>“</div>
        <div style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 52, color: "#f4f2ec", lineHeight: 1.35, textShadow: "0 4px 22px rgba(0,0,0,0.9)" }}>{text}</div>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 3, marginTop: 18 }}>— {kicker}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

/* 08 SIDE NOTE — anotação lateral direita: caixa com borda accent (nota técnica) */
export const Ovl08_SideNote: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ justifyContent: "center" }}>
      <div style={{ position: "absolute", right: 80, maxWidth: 560, background: "rgba(8,9,12,0.74)", backdropFilter: "blur(4px)", borderLeft: `6px solid ${accent}`, borderRadius: "10px 14px 14px 10px", padding: "26px 34px", opacity: s, transform: `translateX(${(1 - s) * 70}px)`, boxShadow: "0 18px 50px rgba(0,0,0,0.5)" }}>
        {kicker ? <div style={{ fontFamily: MONO, fontSize: 22, color: accent, letterSpacing: 4, marginBottom: 10 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: SANS, fontSize: 30, color: "#e8eaee", lineHeight: 1.45 }}>{text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 09 TICKER CAPTION — faixa fina full-width na base (legenda/documental) */
export const Ovl09_TickerCaption: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end" }}>
      <div style={{ background: "rgba(5,6,8,0.82)", borderTop: `3px solid ${accent}`, padding: "20px 90px", display: "flex", alignItems: "center", gap: 26, opacity: s, transform: `translateY(${(1 - s) * 100}%)` }}>
        {kicker ? <span style={{ fontFamily: DISPLAY, fontSize: 26, color: "#0a0b0f", background: accent, padding: "6px 18px", borderRadius: 6, letterSpacing: 2, flexShrink: 0 }}>{kicker.toUpperCase()}</span> : null}
        <span style={{ fontFamily: SANS, fontSize: 30, color: "#eef0f4", lineHeight: 1.35 }}>{text}</span>
      </div>
    </AbsoluteFill>
  );
};

/* 10 NUMBER BADGE — item de lista: número gigante + texto ao lado, baixo-esq */
export const Ovl10_NumberBadge: React.FC<P> = ({ text = "", kicker = "#1", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 13, stiffness: 140 }, durationInFrames: 20 });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(80deg, rgba(0,0,0,0.66) 0%, rgba(0,0,0,0.2) 38%, transparent 60%)" }} />
      <div style={{ position: "absolute", left: 90, bottom: 96, display: "flex", alignItems: "center", gap: 34, opacity: s }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 150, color: accent, lineHeight: 1, textShadow: `0 0 40px ${accent}66`, transform: `scale(${0.5 + 0.5 * s})` }}>{kicker}</div>
        <div style={{ borderLeft: "3px solid rgba(255,255,255,0.35)", paddingLeft: 30 }}>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 52, color: "#fff", maxWidth: 1000, lineHeight: 1.2, textShadow: "0 4px 22px rgba(0,0,0,0.9)" }}>{text}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ============ VIDRUSH PACK (decupagem 14 vídeos, 24/07) — dado NUNCA troca de cena:
   anotações por cima do footage corrente. Contrato continua { text, kicker, accent }. ============ */

/* 11 SPEC BADGE — canto sup-dir estilo `17 • LBS DRAG` (text=valor, kicker=unidade) */
export const Ovl11_SpecBadge: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 130 }, durationInFrames: 18 });
  if (!text) return null;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", right: 70, top: 64, display: "flex", alignItems: "baseline", gap: 16,
        background: "rgba(6,7,10,0.72)", backdropFilter: "blur(4px)", padding: "14px 30px",
        borderRadius: 10, border: "1px solid rgba(255,255,255,0.14)",
        opacity: s, transform: `translateY(${(1 - s) * -24}px)` }}>
        <span style={{ fontFamily: DISPLAY, fontSize: 54, color: "#fff", lineHeight: 1 }}>{text}</span>
        {kicker ? (<>
          <span style={{ fontFamily: SANS, fontSize: 30, color: accent, lineHeight: 1 }}>•</span>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 27, color: "#e8e4da", letterSpacing: 4 }}>{kicker.toUpperCase()}</span>
        </>) : null}
      </div>
    </AbsoluteFill>
  );
};

/* 12 GIANT STAT — número GIGANTE semi-transparente lateral (text=valor, kicker=sub-linha) */
export const Ovl12_GiantStat: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const s = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  if (!text) return null;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(75deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 45%, transparent 70%)" }} />
      <div style={{ position: "absolute", left: 90, top: "50%", transform: `translateY(-50%) translateX(${(1 - s) * -50}px)`, opacity: s }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 230, color: "rgba(255,255,255,0.94)", lineHeight: 0.95,
          textShadow: `0 10px 60px rgba(0,0,0,0.8), 0 0 46px ${accent}44` }}>{text}</div>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 30, color: "#ddd8cc", marginTop: 16, maxWidth: 680, textShadow: "0 3px 16px rgba(0,0,0,0.9)" }}>{kicker}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

/* 13 PRICE TAG — cifra estilizada grande base-dir (text='$450', kicker=contexto curto) */
export const Ovl13_PriceTag: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 20 });
  if (!text) return null;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", right: 84, bottom: 96, textAlign: "right", opacity: s, transform: `scale(${0.86 + s * 0.14})`, transformOrigin: "bottom right" }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 150, color: "#fff", lineHeight: 1,
          textShadow: `0 8px 44px rgba(0,0,0,0.85), 0 0 40px ${accent}66`,
          WebkitTextStroke: `2px ${accent}` }}>{text}</div>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 26, color: "#e8e4da", letterSpacing: 5, marginTop: 10, textShadow: "0 3px 14px rgba(0,0,0,0.9)" }}>{kicker.toUpperCase()}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

/* 14 PILL VERDICT — pill colorida (nome) + caixa fina com veredito de 1 linha (marca de item) */
export const Ovl14_PillVerdict: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 22 });
  const s2 = spring({ frame: Math.max(0, f - 8), fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 22 });
  if (!text) return null;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill style={{ background: "rgba(0,0,0,0.45)" }} />
      <div style={{ opacity: s, transform: `translateY(${(1 - s) * 26}px)`, background: accent, color: "#0c0d10",
        fontFamily: SANS, fontWeight: 800, fontSize: 46, padding: "14px 46px", borderRadius: 12,
        boxShadow: `0 14px 50px rgba(0,0,0,0.6), 0 0 34px ${accent}55`, letterSpacing: 1 }}>{text}</div>
      {kicker ? <div style={{ marginTop: 22, opacity: s2, transform: `translateY(${(1 - s2) * 18}px)`,
        border: `1.5px solid ${accent}bb`, color: "#f2efe6", fontFamily: SANS, fontWeight: 600, fontSize: 28,
        padding: "12px 34px", borderRadius: 8, background: "rgba(6,7,10,0.55)", backdropFilter: "blur(3px)" }}>{kicker}</div> : null}
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO ---------------- */
export const OVERLAY_MANIFEST = [
  { id: 0, comp: "Ovl01_ChapterBig", quando: "abertura de CAPÍTULO sobre footage (kicker='CHAPTER 02')" },
  { id: 1, comp: "Ovl02_SubchapterLine", quando: "SUBCAPÍTULO/tópico discreto no topo" },
  { id: 2, comp: "Ovl03_LowerThird", quando: "lower-third: nome/lugar/rótulo (kicker=função)" },
  { id: 3, comp: "Ovl04_FootnotePill", quando: "NOTA DE RODAPÉ/fonte/disclaimer (kicker='Source')" },
  { id: 4, comp: "Ovl05_CornerTag", quando: "tag de arquivo/época canto sup-dir ('ARCHIVE · 1986')" },
  { id: 5, comp: "Ovl06_CenterPunch", quando: "palavra/frase de impacto central sobre a cena" },
  { id: 6, comp: "Ovl07_QuoteAttribution", quando: "citação falada sobre footage (kicker=autor)" },
  { id: 7, comp: "Ovl08_SideNote", quando: "anotação técnica lateral enquanto a cena roda" },
  { id: 8, comp: "Ovl09_TickerCaption", quando: "legenda documental na base (kicker=etiqueta)" },
  { id: 9, comp: "Ovl10_NumberBadge", quando: "item de lista/ranking (kicker='#3')" },
  { id: 10, comp: "Ovl11_SpecBadge", quando: "spec/número falado sobre o footage ('17 • LBS DRAG')" },
  { id: 11, comp: "Ovl12_GiantStat", quando: "número dramático GIGANTE sobre o footage" },
  { id: 12, comp: "Ovl13_PriceTag", quando: "preço estilizado sobre produto ('$450')" },
  { id: 13, comp: "Ovl14_PillVerdict", quando: "nome do item + veredito de 1 linha" },
];

export const OVERLAY_COMPS: Record<string, React.FC<P>> = {
  Ovl01_ChapterBig, Ovl02_SubchapterLine, Ovl03_LowerThird, Ovl04_FootnotePill, Ovl05_CornerTag,
  Ovl06_CenterPunch, Ovl07_QuoteAttribution, Ovl08_SideNote, Ovl09_TickerCaption, Ovl10_NumberBadge,
  Ovl11_SpecBadge, Ovl12_GiantStat, Ovl13_PriceTag, Ovl14_PillVerdict,
};
