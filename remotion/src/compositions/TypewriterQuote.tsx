import { AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// COLD OPEN dramático: frase filosófica REAL digitada em typewriter sobre fundo chumbo,
// com noise de TV antiga + scanlines + vinheta + flicker. Fonte e SFX de máquina de escrever.

type Props = {
  quote?: string;
  author?: string;
  cps?: number;          // caracteres por segundo (velocidade da digitação)
  typingSfx?: string;    // rel em public/ (default sfx/typewriter.mp3)
};

// ---- noise de TV (ruído animado, contínuo e sutil) ----
const TVNoise: React.FC<{ opacity?: number }> = ({ opacity = 0.08 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity }}>
      <svg width="100%" height="100%">
        <filter id={`tvn${f % 6}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 6} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#tvn${f % 6})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const TypewriterQuote: React.FC<Props> = ({
  quote = "I fear not the man who has practiced 10,000 kicks once, but I fear the man who has practiced one kick 10,000 times.",
  author = "Bruce Lee",
  cps = 20,
  typingSfx = "sfx/typewriter.mp3",
}) => {
  const f = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const shown = Math.max(0, Math.min(quote.length, Math.floor((f / fps) * cps)));
  const typing = shown < quote.length;
  const typedText = quote.slice(0, shown);
  const doneFrame = (quote.length / cps) * fps;

  // cursor pisca
  const cursorOn = Math.floor(f / 8) % 2 === 0;
  // autor entra após terminar de digitar + pausa
  const authorIn = interpolate(f, [doneFrame + fps * 0.5, doneFrame + fps * 1.1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // flicker sutil + fade out no fim
  const flick = 0.95 + 0.05 * Math.abs(Math.sin(f * 1.7));
  const fadeOut = interpolate(f, [durationInFrames - fps * 0.5, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const MONO = "'Courier New', Consolas, 'Lucida Console', monospace";

  return (
    <AbsoluteFill style={{ backgroundColor: "#1b1d22", opacity: fadeOut, fontFamily: MONO }}>
      {/* leve gradiente chumbo */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #262a31 0%, #15171b 75%)" }} />

      {/* SFX de digitação (só enquanto digita) — volume PADRÃO/cheio (pedido Piter 2026-07-01:
          este SFX específico pode ficar no volume default, sem atenuação; estava 0.85, antes 0.6) */}
      {typing && <Audio src={staticFile(typingSfx)} volume={1} />}

      {/* frase + cursor */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 220px", opacity: flick }}>
        <div style={{ fontSize: 60, lineHeight: 1.6, color: "#e6e3da", textAlign: "center", letterSpacing: 1, maxWidth: 1400, textShadow: "0 2px 12px rgba(0,0,0,0.6)" }}>
          {typedText}
          <span style={{ opacity: cursorOn ? 1 : 0, color: "#ff7a3c", fontWeight: 700 }}>▌</span>
        </div>
        {/* autor */}
        <div style={{ marginTop: 64, fontSize: 40, color: "#9aa0ab", letterSpacing: 4, opacity: authorIn, transform: `translateY(${(1 - authorIn) * 14}px)` }}>
          {`— ${author.toUpperCase()}`}
        </div>
      </AbsoluteFill>

      {/* scanlines de TV */}
      <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "multiply", opacity: 0.5,
        backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.5) 0px, rgba(0,0,0,0.5) 1.5px, transparent 3px, transparent 5px)" }} />
      <TVNoise opacity={0.07} />
      {/* vinheta forte (dramático) */}
      <AbsoluteFill style={{ pointerEvents: "none", boxShadow: "inset 0 0 360px 120px rgba(0,0,0,0.9)" }} />
    </AbsoluteFill>
  );
};

// cold-open do TTM hips/silent fear (citação real da Pema Chödrön, tema medo)
export const TypewriterIntro: React.FC = () => (
  <TypewriterQuote
    quote="The central question of a warrior's training is not how we avoid fear and pain but how we encounter it."
    author="Pema Chodron"
  />
);
