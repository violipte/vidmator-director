import React from "react";
import { useCurrentFrame } from "remotion";

/* ============================================================
   KARAOKÊ (v5 F5) — legenda word-by-word no rodapé, sincronizada
   por frames (timing proporcional do beat ou word-level do STT).

   06/08 (QA do Piter): "legenda eterna, com um efeito enjoativo —
   se for deixar legenda, deixe sem esse efeito de EXPLODIR a
   palavra falada". O pop 1.5→1 por palavra saiu; a palavra ativa
   agora se destaca só por COR (a leitura acompanha igual, sem o
   movimento que cansava). A janela também encolheu de 9 pra 6
   palavras: menos texto parado na tela ao mesmo tempo.
   ============================================================ */

export type PalavraK = { word: string; startFrame: number };

export const Karaoke5: React.FC<{ words: PalavraK[]; accent?: string }> = ({ words, accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  if (!words?.length) return null;
  let ativa = 0;
  for (let i = 0; i < words.length; i++) if (f >= words[i].startFrame) ativa = i;
  const ini = Math.max(0, Math.min(ativa - 2, words.length - 6));
  const vis = words.slice(ini, ini + 6);
  return (
    <div style={{
      position: "absolute", left: "50%", bottom: 44, transform: "translateX(-50%)",
      maxWidth: "80%", padding: "12px 26px", borderRadius: 14,
      background: "rgba(4,5,14,0.66)", backdropFilter: "blur(3px)",
      display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 10px",
      pointerEvents: "none",
    }}>
      {vis.map((w, i) => {
        const gi = ini + i;
        const isAtiva = gi === ativa;
        return (
          <span key={gi} style={{
            fontFamily: "Inter, Arial, sans-serif", fontWeight: 700, fontSize: 30,
            color: isAtiva ? accent : gi < ativa ? "rgba(255,255,255,0.82)" : "rgba(255,255,255,0.30)",
            display: "inline-block",
            transition: "color 90ms",
          }}>{w.word}</span>
        );
      })}
    </div>
  );
};
