import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Montserrat";

// Legenda HIPNÓTICA estilo Shorts: agrupa as palavras da narração em frases curtas,
// mostra a frase ativa e DESTACA a palavra sendo falada (cor + leve pop). Só na zona de hook.

const { fontFamily: MONT } = loadFont("normal", { weights: ["600", "800"] });

type W = { word: string; start: number; end: number };

function agrupar(words: W[]): { start: number; end: number; words: W[] }[] {
  const grupos: { start: number; end: number; words: W[] }[] = [];
  let cur: W[] = [];
  for (let i = 0; i < words.length; i++) {
    cur.push(words[i]);
    const next = words[i + 1];
    const gap = next ? next.start - words[i].end : 99;
    if (cur.length >= 3 || gap > 0.45 || !next) {
      grupos.push({ start: cur[0].start, end: cur[cur.length - 1].end, words: cur });
      cur = [];
    }
  }
  return grupos;
}

export const KaraokeCaption: React.FC<{ words: W[]; fonts?: { head?: string } }> = ({ words, fonts }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const grupos = agrupar(words || []);
  const g = grupos.find((gr) => t >= gr.start - 0.15 && t <= gr.end + 0.35);
  if (!g) return null;
  const appear = interpolate(t, [g.start - 0.15, g.start + 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const headFont = MONT;  // Montserrat (sans limpa) — sobrepõe a fonte do tema p/ a legenda do hook
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 250 }}>
      <div style={{ display: "flex", gap: 28, flexWrap: "wrap", justifyContent: "center", maxWidth: "80%", transform: `translateY(${(1 - appear) * 26}px)`, opacity: appear }}>
        {g.words.map((w, i) => {
          const active = t >= w.start - 0.02 && t <= w.end + 0.06;
          const past = t > w.end + 0.06;
          return (
            <span key={i} style={{
              fontFamily: headFont, fontWeight: 900, fontSize: 74, lineHeight: 1.05,
              color: active ? "#fbbf24" : "#ffffff", opacity: past ? 0.82 : 1,
              textShadow: active ? "0 4px 26px rgba(0,0,0,0.95), 0 0 30px rgba(251,191,36,0.5)" : "0 4px 22px rgba(0,0,0,0.95)",
              transform: `scale(${active ? 1.06 : 1})`, display: "inline-block", letterSpacing: 1, textTransform: "uppercase",
            }}>{w.word}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
