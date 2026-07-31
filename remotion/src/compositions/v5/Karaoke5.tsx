import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

/* ============================================================
   KARAOKÊ (v5 F5) — legenda word-by-word no rodapé, sincronizada
   por frames (timing proporcional do beat ou word-level do STT).
   Palavra ativa: accent + pop 1.5→1; passadas: branco 80%;
   futuras: branco 28%. Liga por style_card {"karaoke": true}.
   ============================================================ */

export type PalavraK = { word: string; startFrame: number };

export const Karaoke5: React.FC<{ words: PalavraK[]; accent?: string }> = ({ words, accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  if (!words?.length) return null;
  // janela deslizante: mostra ~9 palavras ao redor da ativa
  let ativa = 0;
  for (let i = 0; i < words.length; i++) if (f >= words[i].startFrame) ativa = i;
  const ini = Math.max(0, Math.min(ativa - 3, words.length - 9));
  const vis = words.slice(ini, ini + 9);
  return (
    <div style={{
      position: "absolute", left: "50%", bottom: 44, transform: "translateX(-50%)",
      maxWidth: "82%", padding: "14px 30px", borderRadius: 16,
      background: "rgba(4,5,14,0.72)", backdropFilter: "blur(3px)",
      display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 10px",
      pointerEvents: "none",
    }}>
      {vis.map((w, i) => {
        const gi = ini + i;
        const isAtiva = gi === ativa;
        const pop = isAtiva
          ? interpolate(f - w.startFrame, [0, 10], [1.5, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
          : 1;
        return (
          <span key={gi} style={{
            fontFamily: "Inter, Arial, sans-serif", fontWeight: 700, fontSize: 30,
            color: isAtiva ? accent : gi < ativa ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.28)",
            transform: `scale(${pop})`, display: "inline-block",
            transition: "color 80ms",
          }}>{w.word}</span>
        );
      })}
    </div>
  );
};
