import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO DE TEXTO — 10 variações NOVAS (2026-07-20).
   CONTRATO ÚNICO: { text, kicker?, accent? } — o Diretor escolhe a
   variação pelo manifesto, troca as variáveis e aplica. Nada além disso.
   ============================================================ */

type P = { text?: string; kicker?: string; accent?: string };
const DISPLAY = F_DISPLAY;
const SERIF = "'Georgia','Times New Roman',serif";
const MONO = F_MONO;
const SANS = F_SANS;
const BG = "#0a0b0f";

/* 01 TYPEWRITER — mono digitando com cursor, dossiê/documento */
export const Texto01_Typewriter: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const n = Math.min(text.length, Math.floor(f / 1.4));
  const cursor = Math.floor(f / 14) % 2 === 0;
  return (
    <AbsoluteFill style={{ background: BG, justifyContent: "center", padding: "0 180px" }}>
      {kicker ? <div style={{ fontFamily: MONO, fontSize: 30, color: accent, letterSpacing: 6, marginBottom: 28 }}>[{kicker.toUpperCase()}]</div> : null}
      <div style={{ fontFamily: MONO, fontSize: 60, color: "#e8e6df", lineHeight: 1.45, textShadow: "0 2px 12px rgba(0,0,0,0.6)" }}>
        {text.slice(0, n)}<span style={{ opacity: cursor ? 1 : 0, color: accent }}>▌</span>
      </div>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0 2px, transparent 2px 4px)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

/* 02 HIGHLIGHT SWEEP — fundo papel, marca-texto varrendo a frase */
export const Texto02_HighlightSweep: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const sweep = interpolate(f, [10, 48], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#f4f1e8", justifyContent: "center", alignItems: "center", padding: "0 160px" }}>
      {kicker ? <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 26, color: "#6b6558", letterSpacing: 8, marginBottom: 30, opacity: op }}>{kicker.toUpperCase()}</div> : null}
      <div style={{ position: "relative", textAlign: "center", opacity: op }}>
        <span style={{
          fontFamily: SERIF, fontSize: 76, fontWeight: 700, color: "#1c1a16", lineHeight: 1.3, padding: "6px 18px",
          backgroundImage: `linear-gradient(${accent}66, ${accent}66)`, backgroundRepeat: "no-repeat",
          backgroundSize: `${sweep}% 46%`, backgroundPosition: "0 78%",
        }}>{text}</span>
      </div>
    </AbsoluteFill>
  );
};

/* 03 WORD POP — kinetic palavra a palavra (spring), display bold */
export const Texto03_WordPop: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 90% 90% at 50% 45%, #14161d 0%, ${BG} 75%)`, justifyContent: "center", alignItems: "center", padding: "0 140px" }}>
      {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 8, marginBottom: 34 }}>{kicker.toUpperCase()}</div> : null}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 26px", maxWidth: 1500 }}>
        {words.map((w, i) => {
          const s = spring({ frame: f - i * 5, fps, config: { damping: 11, stiffness: 160 }, durationInFrames: 18 });
          const destaque = i === words.length - 1;
          return (
            <span key={i} style={{
              fontFamily: DISPLAY, fontSize: 88, lineHeight: 1.25, color: destaque ? accent : "#fff",
              opacity: s, transform: `translateY(${(1 - s) * 46}px) scale(${0.7 + 0.3 * s})`, display: "inline-block",
              textShadow: destaque ? `0 0 34px ${accent}88` : "0 4px 20px rgba(0,0,0,0.6)",
            }}>{w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 04 EDITORIAL SERIF — itálico elegante alinhado à esquerda, régua fina */
export const Texto04_EditorialSerif: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const rule = interpolate(f, [6, 34], [0, 320], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const rise = interpolate(f, [0, 18], [26, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#111214", justifyContent: "center", padding: "0 220px" }}>
      <div style={{ width: rule, height: 3, background: accent, marginBottom: 40 }} />
      {kicker ? <div style={{ fontFamily: SANS, fontSize: 24, fontWeight: 700, color: "#8a8f98", letterSpacing: 10, marginBottom: 22, opacity: op }}>{kicker.toUpperCase()}</div> : null}
      <div style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 78, color: "#f2efe8", lineHeight: 1.35, maxWidth: 1300, opacity: op, transform: `translateY(${rise}px)` }}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

/* 05 BOXED KICKER — caixa técnica com cantoneiras + eyebrow mono */
export const Texto05_BoxedKicker: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const box = interpolate(f, [0, 22], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [14, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const C: React.FC<{ st: React.CSSProperties }> = ({ st }) => (
    <div style={{ position: "absolute", width: 34, height: 34, borderColor: accent, borderStyle: "solid", opacity: box, ...st }} />
  );
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 100% 100% at 50% 50%, #101318 0%, ${BG} 80%)`, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", padding: "70px 110px", transform: `scale(${0.92 + 0.08 * box})` }}>
        <C st={{ top: 0, left: 0, borderWidth: "4px 0 0 4px" }} /><C st={{ top: 0, right: 0, borderWidth: "4px 4px 0 0" }} />
        <C st={{ bottom: 0, left: 0, borderWidth: "0 0 4px 4px" }} /><C st={{ bottom: 0, right: 0, borderWidth: "0 4px 4px 0" }} />
        {kicker ? <div style={{ fontFamily: MONO, fontSize: 28, color: accent, letterSpacing: 8, textAlign: "center", marginBottom: 26, opacity: op }}>{"// " + kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 72, color: "#fff", textAlign: "center", maxWidth: 1200, lineHeight: 1.3, opacity: op }}>{text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 06 SPLIT BAR — barra vertical accent; texto desliza de trás dela */
export const Texto06_SplitBar: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 26 });
  const barH = interpolate(f, [0, 14], [0, 360], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#0d0f13", justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 54, maxWidth: 1500 }}>
        <div style={{ width: 10, height: barH, background: accent, borderRadius: 5, boxShadow: `0 0 30px ${accent}99`, flexShrink: 0 }} />
        <div style={{ overflow: "hidden" }}>
          {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 7, marginBottom: 18, transform: `translateX(${(1 - s) * -110}%)` }}>{kicker.toUpperCase()}</div> : null}
          <div style={{ fontFamily: DISPLAY, fontSize: 80, color: "#fff", lineHeight: 1.25, transform: `translateX(${(1 - s) * -105}%)` }}>{text}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 07 STAMP IMPACT — carimbo: slam com shake curto e rotação */
export const Texto07_StampImpact: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const slam = interpolate(f, [0, 9], [2.6, 1], { extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const shake = f > 9 && f < 17 ? Math.sin(f * 3.1) * (17 - f) * 0.9 : 0;
  const op = interpolate(f, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 85% at 50% 48%, #191512 0%, #0b0908 78%)`, justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `scale(${slam}) rotate(${-3 + shake * 0.4}deg) translateX(${shake}px)`, opacity: op, textAlign: "center", padding: "40px 80px", border: `6px solid ${accent}`, borderRadius: 10, boxShadow: `0 0 60px ${accent}44, inset 0 0 40px rgba(0,0,0,0.5)` }}>
        {kicker ? <div style={{ fontFamily: DISPLAY, fontSize: 30, color: accent, letterSpacing: 10, marginBottom: 14 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 96, color: "#f3efe9", lineHeight: 1.15, maxWidth: 1250, textTransform: "uppercase" }}>{text}</div>
      </div>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 4px)", opacity: 0.5, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

/* 08 GRADIENT GLOW — bold com gradiente animado + brilho */
export const Texto08_GradientGlow: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const pos = (f * 1.8) % 200;
  const pulse = 0.75 + 0.25 * Math.sin(f / 9);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 80% at 50% 50%, #131018 0%, ${BG} 80%)`, justifyContent: "center", alignItems: "center", padding: "0 150px" }}>
      {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: "#9aa0ab", letterSpacing: 9, marginBottom: 30, opacity: op }}>{kicker.toUpperCase()}</div> : null}
      <div style={{
        fontFamily: DISPLAY, fontSize: 100, lineHeight: 1.2, textAlign: "center", maxWidth: 1500, opacity: op,
        backgroundImage: `linear-gradient(100deg, #ffffff 20%, ${accent} 45%, #ffdf9e 55%, #ffffff 80%)`,
        backgroundSize: "200% 100%", backgroundPosition: `${pos}% 0`,
        WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent",
        filter: `drop-shadow(0 0 ${24 * pulse}px ${accent}66)`,
      }}>{text}</div>
    </AbsoluteFill>
  );
};

/* 09 UNDERLINE DRAW — minimal clean; sublinhado desenhando sob a última palavra */
export const Texto09_UnderlineDraw: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const draw = interpolate(f, [16, 40], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const words = text.split(/\s+/).filter(Boolean);
  const resto = words.slice(0, -1).join(" ");
  const ult = words[words.length - 1] || "";
  return (
    <AbsoluteFill style={{ background: "#101114", justifyContent: "center", alignItems: "center", padding: "0 170px" }}>
      {kicker ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 24, color: "#7d828c", letterSpacing: 11, marginBottom: 34, opacity: op }}>{kicker.toUpperCase()}</div> : null}
      <div style={{ fontFamily: SANS, fontWeight: 300, fontSize: 78, color: "#eceef2", lineHeight: 1.35, textAlign: "center", maxWidth: 1400, opacity: op }}>
        {resto}{" "}
        <span style={{ position: "relative", fontWeight: 800, whiteSpace: "nowrap" }}>
          {ult}
          <span style={{ position: "absolute", left: 0, bottom: -10, height: 7, width: `${draw}%`, background: accent, borderRadius: 4, boxShadow: `0 0 16px ${accent}88` }} />
        </span>
      </div>
    </AbsoluteFill>
  );
};

/* 10 LETTER CASCADE — letras entrando uma a uma (blur -> nítido) */
export const Texto10_LetterCascade: React.FC<P> = ({ text = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const chars = text.split("");
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, #0e1015 0%, #16121c 100%)`, justifyContent: "center", alignItems: "center", padding: "0 140px" }}>
      {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 8, marginBottom: 32, opacity: interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" }) }}>{kicker.toUpperCase()}</div> : null}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", maxWidth: 1500 }}>
        {chars.map((c, i) => {
          const o = interpolate(f, [i * 1.1, i * 1.1 + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const bl = interpolate(o, [0, 1], [10, 0]);
          return (
            <span key={i} style={{ fontFamily: DISPLAY, fontSize: 86, color: "#f4f2ec", lineHeight: 1.25, opacity: o, filter: `blur(${bl}px)`, whiteSpace: "pre", textShadow: "0 4px 22px rgba(0,0,0,0.55)" }}>{c}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO do almoxarifado (o Diretor lê isto) ---------------- */
export const TEXTO_MANIFEST = [
  { id: 0, comp: "Texto01_Typewriter", quando: "documento/dossiê, fato seco, tom investigativo" },
  { id: 1, comp: "Texto02_HighlightSweep", quando: "citação de estudo/artigo, frase com trecho-chave" },
  { id: 2, comp: "Texto03_WordPop", quando: "frase de impacto curta, punchline, hook" },
  { id: 3, comp: "Texto04_EditorialSerif", quando: "reflexão, transição elegante, tom documentário" },
  { id: 4, comp: "Texto05_BoxedKicker", quando: "spec/definição técnica, dado nomeado" },
  { id: 5, comp: "Texto06_SplitBar", quando: "afirmação direta, abertura de tópico" },
  { id: 6, comp: "Texto07_StampImpact", quando: "veredito, conclusão forte, palavra de ordem" },
  { id: 7, comp: "Texto08_GradientGlow", quando: "momento épico/premium, número ou frase-troféu" },
  { id: 8, comp: "Texto09_UnderlineDraw", quando: "frase com UMA palavra decisiva no fim" },
  { id: 9, comp: "Texto10_LetterCascade", quando: "revelação gradual, suspense, nome próprio" },
];

export const TEXTO_COMPS: Record<string, React.FC<P>> = {
  Texto01_Typewriter, Texto02_HighlightSweep, Texto03_WordPop, Texto04_EditorialSerif,
  Texto05_BoxedKicker, Texto06_SplitBar, Texto07_StampImpact, Texto08_GradientGlow,
  Texto09_UnderlineDraw, Texto10_LetterCascade,
};
