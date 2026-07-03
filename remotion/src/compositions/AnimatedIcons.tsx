import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

// Ícones de CONCEITO animados (line-art, draw-on) — niche-agnósticos.
// ICON_RENDERERS é a fonte compartilhada (galeria + Illustration de produção).

const STROKE = "#e9eef7";
const ACCENT = "#fbbf24";
const H = 1080;
const LOOP = 130;

const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));
const dash = (p: number) => ({ pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - p } as any);
const S = { fill: "none", stroke: STROKE, strokeWidth: 5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

// renderiza em viewBox 0 0 120 120; p = 0..1. cor do traço herda currentColor onde STROKE é usado.
export const ICON_RENDERERS: Record<string, (p: number) => React.ReactNode> = {
  ideia: (p) => (
    <g>
      <path d="M60 22 C 40 22, 28 38, 32 56 C 35 68, 48 74, 48 86 L 72 86 C 72 74, 85 68, 88 56 C 92 38, 80 22, 60 22 Z" {...S} {...dash(seg(p, 0, 0.6))} />
      <path d="M50 94 L 70 94 M53 102 L 67 102" {...S} {...dash(seg(p, 0.5, 0.8))} />
      {[-36, 0, 36].map((a, i) => (
        <line key={i} transform={`rotate(${a} 60 30)`} x1={60} y1={6} x2={60} y2={-2} {...S} stroke={ACCENT} {...dash(seg(p, 0.7, 1))} />
      ))}
    </g>
  ),
  mente: (p) => (
    <g>
      <path d="M64 28 C 44 24, 30 38, 32 54 C 24 60, 26 76, 38 80 C 42 92, 60 92, 64 84 L 64 28 Z" {...S} {...dash(seg(p, 0, 0.55))} />
      <path d="M64 30 C 84 26, 96 40, 92 54 C 100 60, 96 76, 84 80 C 80 92, 66 92, 64 84" {...S} {...dash(seg(p, 0.2, 0.8))} />
      <path d="M50 46 C 44 50, 46 56, 52 56 M72 46 C 78 50, 76 56, 70 56 M48 66 C 44 70, 48 74, 54 72 M74 66 C 80 70, 74 74, 68 72" {...S} stroke={ACCENT} strokeWidth={3.5} {...dash(seg(p, 0.6, 1))} />
    </g>
  ),
  saude: (p) => (
    <g>
      <path d="M60 92 C 30 70, 18 52, 30 38 C 40 26, 56 32, 60 44 C 64 32, 80 26, 90 38 C 102 52, 90 70, 60 92 Z" {...S} {...dash(seg(p, 0, 0.7))} />
      <path d="M28 60 L 46 60 L 54 46 L 64 74 L 72 60 L 92 60" {...S} stroke={ACCENT} {...dash(seg(p, 0.55, 1))} />
    </g>
  ),
  dinheiro: (p) => (
    <g>
      <circle cx={60} cy={60} r={34} {...S} {...dash(seg(p, 0, 0.6))} />
      <path d="M72 46 C 66 40, 50 40, 50 50 C 50 60, 70 60, 70 70 C 70 80, 54 80, 48 74" {...S} stroke={ACCENT} {...dash(seg(p, 0.5, 0.95))} />
      <line x1={60} y1={34} x2={60} y2={86} {...S} stroke={ACCENT} {...dash(seg(p, 0.8, 1))} />
    </g>
  ),
  tempo: (p) => (
    <g>
      <circle cx={60} cy={60} r={34} {...S} {...dash(seg(p, 0, 0.6))} />
      <line x1={60} y1={60} x2={60} y2={38} {...S} stroke={ACCENT} {...dash(seg(p, 0.55, 0.8))} />
      <line x1={60} y1={60} x2={78} y2={66} {...S} stroke={ACCENT} {...dash(seg(p, 0.75, 1))} />
      <circle cx={60} cy={60} r={3.5} fill={ACCENT} stroke="none" opacity={seg(p, 0.6, 0.8)} />
    </g>
  ),
  crescimento: (p) => (
    <g>
      <path d="M26 26 L 26 94 L 96 94" {...S} {...dash(seg(p, 0, 0.4))} />
      <path d="M34 80 L 52 64 L 66 72 L 90 40" {...S} stroke={ACCENT} {...dash(seg(p, 0.35, 0.85))} />
      <path d="M78 40 L 90 40 L 90 52" {...S} stroke={ACCENT} {...dash(seg(p, 0.8, 1))} />
    </g>
  ),
  pessoas: (p) => (
    <g>
      <circle cx={44} cy={46} r={13} {...S} {...dash(seg(p, 0, 0.4))} />
      <path d="M24 92 C 24 70, 64 70, 64 92" {...S} {...dash(seg(p, 0.25, 0.6))} />
      <circle cx={78} cy={50} r={11} {...S} stroke={ACCENT} {...dash(seg(p, 0.45, 0.75))} />
      <path d="M64 92 C 64 74, 98 74, 98 92" {...S} stroke={ACCENT} {...dash(seg(p, 0.65, 1))} />
    </g>
  ),
  meta: (p) => (
    <g>
      <circle cx={60} cy={60} r={34} {...S} {...dash(seg(p, 0, 0.45))} />
      <circle cx={60} cy={60} r={21} {...S} {...dash(seg(p, 0.3, 0.7))} />
      <circle cx={60} cy={60} r={8} {...S} stroke={ACCENT} {...dash(seg(p, 0.6, 0.9))} />
      <circle cx={60} cy={60} r={3.5} fill={ACCENT} stroke="none" opacity={seg(p, 0.85, 1)} />
    </g>
  ),
  seguranca: (p) => (
    <g>
      <path d="M60 22 L 92 34 L 92 62 C 92 84, 74 94, 60 98 C 46 94, 28 84, 28 62 L 28 34 Z" {...S} {...dash(seg(p, 0, 0.65))} />
      <path d="M46 60 L 56 70 L 76 46" {...S} stroke={ACCENT} {...dash(seg(p, 0.55, 1))} />
    </g>
  ),
  risco: (p) => (
    <g>
      <path d="M60 24 L 98 92 L 22 92 Z" {...S} {...dash(seg(p, 0, 0.7))} />
      <line x1={60} y1={48} x2={60} y2={72} {...S} stroke={ACCENT} {...dash(seg(p, 0.6, 0.9))} />
      <circle cx={60} cy={82} r={3.5} fill={ACCENT} stroke="none" opacity={seg(p, 0.85, 1)} />
    </g>
  ),
  lancamento: (p) => (
    <g>
      <path d="M60 22 C 74 34, 78 56, 72 76 L 48 76 C 42 56, 46 34, 60 22 Z" {...S} {...dash(seg(p, 0, 0.5))} />
      <circle cx={60} cy={48} r={7} {...S} {...dash(seg(p, 0.4, 0.65))} />
      <path d="M48 70 L 36 84 L 48 80 M72 70 L 84 84 L 72 80" {...S} {...dash(seg(p, 0.55, 0.8))} />
      <path d="M54 80 C 56 90, 64 90, 66 80" {...S} stroke={ACCENT} {...dash(seg(p, 0.75, 1))} />
    </g>
  ),
  atencao: (p) => (
    <g>
      <path d="M22 60 C 40 38, 80 38, 98 60 C 80 82, 40 82, 22 60 Z" {...S} {...dash(seg(p, 0, 0.6))} />
      <circle cx={60} cy={60} r={13} {...S} stroke={ACCENT} {...dash(seg(p, 0.5, 0.85))} />
      <circle cx={60} cy={60} r={4} fill={ACCENT} stroke="none" opacity={seg(p, 0.8, 1)} />
    </g>
  ),
};

export const ICON_KEYS = Object.keys(ICON_RENDERERS);
const NOMES: Record<string, string> = {
  ideia: "Ideia", mente: "Mente", saude: "Saúde", dinheiro: "Dinheiro", tempo: "Tempo",
  crescimento: "Crescimento", pessoas: "Pessoas", meta: "Meta", seguranca: "Segurança",
  risco: "Risco", lancamento: "Lançamento", atencao: "Atenção",
};

const Cell: React.FC<{ k: string; idx: number }> = ({ k, idx }) => {
  const frame = useCurrentFrame();
  const local = (frame + idx * 3) % LOOP;
  const p = interpolate(local, [8, 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fade = interpolate(local, [0, 8, LOOP - 14, LOOP - 2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pop = interpolate(local, [8, 20], [0.9, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14, opacity: fade }}>
      <svg width={150} height={150} viewBox="0 0 120 120" style={{ transform: `scale(${pop})` }}>
        {ICON_RENDERERS[k](p)}
      </svg>
      <div style={{ color: "#9aa7b8", fontFamily: "'Segoe UI',system-ui,sans-serif", fontSize: 22, marginTop: 6 }}>{NOMES[k]}</div>
    </div>
  );
};

export const AnimatedIcons: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0e1626 0%, #05070d 100%)", padding: 50 }}>
      <div style={{ color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", fontWeight: 700, fontSize: 40, textAlign: "center", marginBottom: 26 }}>
        Ícones de conceito — ilustram explicações (qualquer nicho)
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gridTemplateRows: "repeat(3, 1fr)", gap: 22, height: H - 180 }}>
        {ICON_KEYS.map((k, i) => <Cell key={k} k={k} idx={i} />)}
      </div>
    </AbsoluteFill>
  );
};
