import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

/* ============================================================
   IMAGE EFFECTS (v5 F3) — camadas CSS por cima do beat, SEM
   assets de vídeo e SEM decode (alívio direto no gargalo de
   render). 10 efeitos absorvidos do dark-content-studio:
   grades: tealOrange · duotone · silverGrade · warmGrade ·
           coldGrade · vignette
   animados: filmGrain · lightLeak · glowPulse · flashBurst
   ============================================================ */

export type FxImg = { tipo: string; accent?: string };

export const ImageEffect5: React.FC<FxImg> = ({ tipo, accent = "#f59e0b" }) => {
  const f = useCurrentFrame();

  if (tipo === "tealOrange") {
    return (
      <>
        <AbsoluteFill style={{ background: "rgba(0,200,180,0.16)", mixBlendMode: "screen", pointerEvents: "none" }} />
        <AbsoluteFill style={{ background: "rgba(255,120,0,0.16)", mixBlendMode: "multiply", pointerEvents: "none" }} />
      </>
    );
  }
  if (tipo === "duotone") {
    return (
      <AbsoluteFill style={{
        background: `linear-gradient(135deg, ${accent}55 0%, transparent 45%, rgba(4,5,14,0.5) 100%)`,
        mixBlendMode: "screen", pointerEvents: "none",
      }} />
    );
  }
  if (tipo === "silverGrade") {
    return <AbsoluteFill style={{ background: "rgba(150,160,175,0.3)", mixBlendMode: "color", pointerEvents: "none" }} />;
  }
  if (tipo === "warmGrade") {
    return <AbsoluteFill style={{ background: "linear-gradient(0deg, rgba(255,120,0,0.22) 0%, transparent 65%)", pointerEvents: "none" }} />;
  }
  if (tipo === "coldGrade") {
    return <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,100,255,0.20) 0%, transparent 60%)", pointerEvents: "none" }} />;
  }
  if (tipo === "vignette") {
    return <AbsoluteFill style={{ background: "radial-gradient(ellipse 75% 75% at 50% 50%, transparent 55%, rgba(0,0,0,0.62) 100%)", pointerEvents: "none" }} />;
  }
  if (tipo === "filmGrain") {
    // grão procedural: 3 padrões alternando a cada 3 frames (sem asset)
    const seed = Math.floor(f / 3) % 3;
    const grains = [
      "repeating-conic-gradient(rgba(255,255,255,0.05) 0deg 1deg, transparent 1deg 3deg)",
      "repeating-conic-gradient(rgba(255,255,255,0.045) 0.5deg 1.5deg, transparent 1.5deg 3.5deg)",
      "repeating-conic-gradient(rgba(255,255,255,0.055) 0.2deg 1.2deg, transparent 1.2deg 2.8deg)",
    ];
    return (
      <AbsoluteFill style={{
        background: grains[seed], backgroundSize: "180px 180px",
        backgroundPosition: `${(seed * 61) % 120}px ${(seed * 37) % 90}px`,
        mixBlendMode: "screen", opacity: 0.55, pointerEvents: "none",
      }} />
    );
  }
  if (tipo === "lightLeak") {
    // 2 streaks varrendo em velocidades diferentes (quente esq→dir, fria dir→esq)
    const x1 = interpolate(f % 240, [0, 240], [-40, 130]);
    const x2 = interpolate(f % 300, [0, 300], [120, -50]);
    return (
      <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
        <div style={{ position: "absolute", top: 0, bottom: 0, left: `${x1}%`, width: "34%",
          background: "linear-gradient(100deg, transparent, rgba(255,140,40,0.22), transparent)" }} />
        <div style={{ position: "absolute", top: 0, bottom: 0, left: `${x2}%`, width: "20%",
          background: "linear-gradient(80deg, transparent, rgba(80,200,255,0.16), transparent)" }} />
      </AbsoluteFill>
    );
  }
  if (tipo === "glowPulse") {
    const r = 30 + 12 * Math.sin(f * 0.08);
    const op = 0.15 + 0.1 * (0.5 + 0.5 * Math.sin(f * 0.08));
    return (
      <AbsoluteFill style={{
        background: `radial-gradient(circle ${r}% at 50% 46%, ${accent}66, transparent 70%)`,
        opacity: op, mixBlendMode: "screen", pointerEvents: "none",
      }} />
    );
  }
  if (tipo === "flashBurst") {
    // flash a cada ~2s: sobe em 4f, decai em 12f
    const ciclo = f % 60;
    const op = ciclo < 4 ? interpolate(ciclo, [0, 4], [0, 0.5])
      : ciclo < 16 ? interpolate(ciclo, [4, 16], [0.5, 0]) : 0;
    return <AbsoluteFill style={{ background: "#fff", opacity: op, pointerEvents: "none" }} />;
  }
  return null;
};

export const FX_IMG_GRADES = ["tealOrange", "duotone", "silverGrade", "warmGrade", "coldGrade", "vignette"];
export const FX_IMG_ANIMADOS = ["filmGrain", "lightLeak", "glowPulse", "flashBurst"];
