import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/* ============================================================
   ALMOXARIFADO DE LISTAS — VidRush pack (decupagem 14 vídeos, 24/07).
   Checklist de nota manuscrita + painel lateral de bullets sobre footage.
   Contrato: { title?, items: string[], kicker?, accent? }.
   Prefixo "Lst" NÃO conta como família texto (é visual de dado, como chart).
   ============================================================ */

type P = { title?: string; items?: string[]; kicker?: string; accent?: string };
const DISPLAY = F_DISPLAY;
const SANS = F_SANS;
const MONO = F_MONO;
const SCRIPT = "'Segoe Print','Comic Sans MS',cursive";

/* 01 NOTE CHECKLIST — card de nota creme com ✓s manuscritos, leve rotação.
   Ref.: 'CENTRON: BUDGET BENCHMARK', 'WHY CEYMAR C-10 WINS'. */
export const Lst01_NoteChecklist: React.FC<P> = ({ title = "", items = [], accent = "#b45309" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const its = items.filter(Boolean).slice(0, 5);
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 22 });
  if (!title || its.length < 2) return null;
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #171410 0%, #0c0a08 100%)", alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(220,205,170,0.05) 0 1px, transparent 1px 52px), repeating-linear-gradient(90deg, rgba(220,205,170,0.05) 0 1px, transparent 1px 52px)" }} />
      <div style={{ background: "#f4efe1", borderRadius: 6, padding: "54px 74px", transform: `rotate(-1.4deg) translateY(${(1 - s) * 50}px)`, opacity: s,
        boxShadow: "0 34px 90px rgba(0,0,0,0.7)", backgroundImage: "repeating-linear-gradient(0deg, transparent 0 45px, rgba(120,100,70,0.16) 45px 46px)" }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 44, color: "#241f16", marginBottom: 30, borderBottom: "3px solid #241f16", paddingBottom: 12, letterSpacing: 1 }}>{title.toUpperCase()}</div>
        {its.map((it, i) => {
          const op = interpolate(f, [14 + i * 8, 26 + i * 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 20, opacity: op, marginBottom: 8, minHeight: 46 }}>
              <span style={{ fontFamily: SCRIPT, fontSize: 36, color: accent, fontWeight: 700 }}>✓</span>
              <span style={{ fontFamily: SCRIPT, fontSize: 29, color: "#33291c" }}>{it}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 02 SIDE PANEL LIST — painel direito escuro com bullets; esquerda TRANSPARENTE (montador dá bg).
   Ref.: 'EGR Failure Modes', 'Compliance and Market Risks'. */
export const Lst02_SidePanelList: React.FC<P> = ({ title = "", items = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const its = items.filter(Boolean).slice(0, 5);
  const s = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  if (!title || its.length < 2) return null;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: "38%",
        background: "linear-gradient(180deg, rgba(8,9,12,0.94) 0%, rgba(10,11,15,0.90) 100%)",
        borderLeft: `3px solid ${accent}`, padding: "90px 60px 60px 56px",
        transform: `translateX(${(1 - s) * 100}%)` }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 46, color: "#fff", lineHeight: 1.15, marginBottom: 40 }}>{title}</div>
        {its.map((it, i) => {
          const op = interpolate(f, [16 + i * 9, 30 + i * 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ display: "flex", gap: 16, opacity: op, marginBottom: 22 }}>
              <span style={{ fontFamily: MONO, fontSize: 24, color: accent, lineHeight: 1.5 }}>▸</span>
              <span style={{ fontFamily: SANS, fontWeight: 500, fontSize: 26, color: "#ddd8cc", lineHeight: 1.45 }}>{it}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const LISTA_MANIFEST = [
  { id: 0, comp: "Lst01_NoteChecklist", quando: "critérios/razões como checklist manuscrito (2-5 itens)" },
  { id: 1, comp: "Lst02_SidePanelList", quando: "bullets técnicos ao lado do footage corrente (2-5 itens)" },
];

export const LISTA_COMPS: Record<string, React.FC<P>> = { Lst01_NoteChecklist, Lst02_SidePanelList };
