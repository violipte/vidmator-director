import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

// Galeria de DOODLES (rabiscos hand-drawn) com draw-on animado p/ o usuário escolher.
// Cada doodle é SVG com pathLength=1 -> strokeDasharray controla o "desenhar".
// Um filtro feTurbulence dá leve tremor de marcador (look feito à mão).

const ACCENT = "#facc15"; // marcador (calibrável)
const W = 1920, H = 1080;
const LOOP = 120; // frames por ciclo (~4s)

const dash = (p: number) => ({ pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - p } as any);
const common = { fill: "none", stroke: ACCENT, strokeWidth: 7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, filter: "url(#rough)" };

// cada doodle recebe progress 0..1 e desenha sobre um "assunto" no centro da célula (0..360 x 0..220)
const DOODLES: { nome: string; subj: string; draw: (p: number) => React.ReactNode }[] = [
  {
    nome: "Círculo (destaque)", subj: "FOCO",
    draw: (p) => (
      // elipse "à mão" com overshoot (começa e passa do ponto de partida)
      <path d="M250 60 C 120 35, 70 95, 95 140 C 120 185, 250 195, 300 150 C 335 118, 300 55, 175 52" {...common} {...dash(p)} />
    ),
  },
  {
    nome: "Sublinhado", subj: "verdade",
    draw: (p) => (
      <path d="M70 165 C 160 150, 250 178, 330 160" {...common} {...dash(p)} />
    ),
  },
  {
    nome: "Sublinhado duplo", subj: "agora",
    draw: (p) => (
      <g>
        <path d="M75 158 C 160 145, 250 170, 320 152" {...common} {...dash(Math.min(1, p * 1.6))} />
        <path d="M85 178 C 165 168, 250 188, 315 172" {...common} {...dash(Math.max(0, (p - 0.35) * 1.6))} />
      </g>
    ),
  },
  {
    nome: "Seta (curva)", subj: "olhe",
    draw: (p) => (
      <g>
        <path d="M40 40 C 130 70, 90 150, 175 150" {...common} {...dash(Math.min(1, p * 1.4))} />
        <path d="M150 128 L 182 152 L 150 175" {...common} {...dash(Math.max(0, (p - 0.6) * 2.5))} />
      </g>
    ),
  },
  {
    nome: "Rabisco (ênfase)", subj: "energia",
    draw: (p) => (
      <path d="M60 150 L 110 130 L 150 168 L 200 128 L 245 170 L 295 130 L 335 160" {...common} {...dash(p)} />
    ),
  },
  {
    nome: "Riscar (cortar)", subj: "medo",
    draw: (p) => (
      <path d="M60 130 C 160 110, 250 150, 335 122" {...common} strokeWidth={8} {...dash(p)} />
    ),
  },
  {
    nome: "Retângulo (caixa)", subj: "chave",
    draw: (p) => (
      <path d="M55 55 L 320 48 L 328 168 L 62 178 Z" {...common} {...dash(p)} />
    ),
  },
  {
    nome: "Check (certo)", subj: "sim",
    draw: (p) => (
      <path d="M130 120 L 175 168 L 280 60" {...common} strokeWidth={9} {...dash(p)} />
    ),
  },
  {
    nome: "Colchetes", subj: "isto",
    draw: (p) => (
      <g>
        <path d="M95 50 C 70 50, 70 50, 68 70 L 64 150 C 64 170, 70 172, 95 172" {...common} {...dash(Math.min(1, p * 1.5))} />
        <path d="M300 50 C 325 50, 325 50, 327 70 L 331 150 C 331 170, 325 172, 300 172" {...common} {...dash(Math.max(0, (p - 0.3) * 1.5))} />
      </g>
    ),
  },
];

const Cell: React.FC<{ d: typeof DOODLES[0]; idx: number }> = ({ d, idx }) => {
  const frame = useCurrentFrame();
  const local = (frame + idx * 4) % LOOP;
  const p = interpolate(local, [10, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fade = interpolate(local, [0, 8, LOOP - 14, LOOP - 2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14 }}>
      <div style={{ position: "relative", width: 360, height: 220 }}>
        {/* assunto (palavra de exemplo) */}
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
          color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", fontWeight: 800, fontSize: 56, letterSpacing: 1 }}>
          {d.subj}
        </div>
        {/* doodle por cima */}
        <svg width={360} height={220} viewBox="0 0 360 220" style={{ position: "absolute", inset: 0, opacity: fade }}>
          {d.draw(p)}
        </svg>
      </div>
      <div style={{ color: "#9aa7b8", fontFamily: "'Segoe UI',system-ui,sans-serif", fontSize: 22, marginTop: 4 }}>{d.nome}</div>
    </div>
  );
};

export const DoodleGallery: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0e1626 0%, #05070d 100%)", padding: 50 }}>
      {/* filtro de tremor "marcador" */}
      <svg width={0} height={0}>
        <filter id="rough">
          <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves={2} seed={7} result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale={5} />
        </filter>
      </svg>
      <div style={{ color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", fontWeight: 700, fontSize: 40, textAlign: "center", marginBottom: 28 }}>
        Doodles / rabiscos — amostra de estilos
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gridTemplateRows: "repeat(3, 1fr)", gap: 22, height: H - 180 }}>
        {DOODLES.map((d, i) => <Cell key={i} d={d} idx={i} />)}
      </div>
    </AbsoluteFill>
  );
};
