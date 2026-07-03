import { AbsoluteFill, Audio, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import sfxLib from "../sfx_lib.json";

// Sampler de SFX p/ AVALIAÇÃO: toca cada efeito com um card (categoria + nome + uso sugerido).
// Biblioteca gerada por ai33.pro (gerar_sfx.py) -> manifesto src/sfx_lib.json.

const FONT = "'Segoe UI', system-ui, sans-serif";
const COR: Record<string, string> = {
  "TRANSIÇÃO": "#38bdf8", "SINO": "#fbbf24", "WHOOSH": "#34d399",
  "SWISH": "#a78bfa", "GLITCH": "#f87171", "NOISE": "#fb923c",
};

const SFX = (sfxLib as { nome: string; cat: string; uso: string; rel: string }[]).map((s) => ({
  cat: s.cat, nome: s.nome.replace(/_/g, " "), rel: s.rel, uso: s.uso,
}));

const SLIDE = 60; // 2s cada
const PLAY = 10;   // toca no frame 10

const Card: React.FC<{ s: typeof SFX[0]; idx: number }> = ({ s, idx }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cor = COR[s.cat] || "#fff";
  const inn = spring({ frame, fps, config: { damping: 16, stiffness: 120 }, durationInFrames: 12 });
  const out = interpolate(frame, [SLIDE - 8, SLIDE], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = Math.min(inn, out);
  // pulso quando o som bate
  const pulse = Math.max(0, 1 - Math.abs(frame - PLAY) / 10);
  const ring = interpolate(Math.max(0, frame - PLAY), [0, 22], [0.3, 1.5], { extrapolateRight: "clamp" });
  const ringOp = interpolate(Math.max(0, frame - PLAY), [0, 22], [0.7, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #141b27, #070b12)", justifyContent: "center", alignItems: "center", opacity: op }}>
      <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", transform: `translateY(${(1 - inn) * 30}px)` }}>
        <div style={{ position: "relative", width: 200, height: 200, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 30 }}>
          <div style={{ position: "absolute", width: 160, height: 160, borderRadius: "50%", border: `4px solid ${cor}`, transform: `scale(${ring})`, opacity: ringOp }} />
          <div style={{ width: 150, height: 150, borderRadius: "50%", background: cor, opacity: 0.16 + pulse * 0.4, transform: `scale(${1 + pulse * 0.18})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 70, color: cor }}>♪</span>
          </div>
        </div>
        <div style={{ background: cor, color: "#0b1020", fontFamily: FONT, fontWeight: 900, fontSize: 22, letterSpacing: 2, padding: "6px 18px", borderRadius: 20 }}>{s.cat}</div>
        <div style={{ color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 64, marginTop: 18 }}>{idx + 1}. {s.nome}</div>
        <div style={{ color: "#9fb0c4", fontFamily: FONT, fontSize: 30, marginTop: 6 }}>{s.uso}</div>
      </div>
      <Sequence from={PLAY} durationInFrames={SLIDE - PLAY}>
        <Audio src={staticFile(s.rel)} volume={0.9} />
      </Sequence>
    </AbsoluteFill>
  );
};

export const SfxSampler: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    {SFX.map((s, i) => (
      <Sequence key={i} from={i * SLIDE} durationInFrames={SLIDE}>
        <Card s={s} idx={i} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
