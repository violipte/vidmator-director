import React from "react";
import { AbsoluteFill } from "remotion";
import { TEMAS, FonteTema } from "../fontes";

/* Prancha de curadoria dos temas tipográficos (R-107) — 1 frame, 4 quadrantes. */

const NICHOS: Record<FonteTema, string> = {
  impact: "true crime · automotivo · choque",
  serif: "história · biografia · filosofia",
  typewriter: "mistério · dossiê · investigação",
  clean: "saúde · ciência · explicativo",
};

const Quadrante: React.FC<{ tema: FonteTema; accent: string }> = ({ tema, accent }) => {
  const t = TEMAS[tema];
  return (
    <div style={{ width: "50%", height: "50%", padding: 46, boxSizing: "border-box",
      borderRight: "1px solid #222b3a", borderBottom: "1px solid #222b3a",
      display: "flex", flexDirection: "column", background: "radial-gradient(ellipse 90% 90% at 50% 40%, #0d1420 0%, #070b12 100%)" }}>
      <div style={{ fontFamily: t.mono, fontSize: 22, color: accent, letterSpacing: 4 }}>
        {tema.toUpperCase()} — {NICHOS[tema]}
      </div>
      <div style={{ fontFamily: t.display, fontSize: 64, color: "#fff", lineHeight: 1.05, marginTop: 18 }}>
        THE MACHINE THAT REFUSED TO DIE
      </div>
      <div style={{ fontFamily: t.body, fontSize: 27, color: "#c9d2e0", marginTop: 16, lineHeight: 1.45 }}>
        By the end of the study, only fifteen percent of the runners had died — the people
        everyone expected to break down were dying at half the rate.
      </div>
      <div style={{ marginTop: "auto", display: "flex", alignItems: "baseline", gap: 26 }}>
        <span style={{ fontFamily: t.display, fontSize: 84, color: accent }}>15%</span>
        <span style={{ fontFamily: t.body, fontSize: 26, color: "#8a94a6" }}>vs 34%</span>
        <span style={{ fontFamily: t.mono, fontSize: 21, color: "#7d94b8", marginLeft: "auto", letterSpacing: 3 }}>
          CHAPTER 03 · 1984
        </span>
      </div>
    </div>
  );
};

export const FontePrancha: React.FC = () => (
  <AbsoluteFill style={{ background: "#05070c", flexDirection: "row", flexWrap: "wrap" }}>
    <Quadrante tema="impact" accent="#f59e0b" />
    <Quadrante tema="serif" accent="#d4a24e" />
    <Quadrante tema="typewriter" accent="#c8452c" />
    <Quadrante tema="clean" accent="#38bdf8" />
  </AbsoluteFill>
);
