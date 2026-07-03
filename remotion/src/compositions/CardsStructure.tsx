import { AbsoluteFill, interpolate, Easing, useCurrentFrame } from "remotion";

// Cards & estrutura — pra organizar/explicar informação (qualquer nicho).

const ACCENT = "#fbbf24";
const ACCENT2 = "#38bdf8";
const TXT = "#eef4fc";
const SUB = "#9aa7b8";
const H = 1080;
const LOOP = 150;
const FONT = "'Segoe UI',system-ui,sans-serif";

const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));

// ---- 1. Lower-third (fato) ----
const LowerThird: React.FC<{ p: number }> = ({ p }) => {
  const slide = interpolate(seg(p, 0, 0.5), [0, 1], [-50, 0]);
  return (
    <div style={{ opacity: seg(p, 0, 0.4), transform: `translateX(${slide}px)`, display: "flex", alignItems: "center",
      background: "rgba(8,14,24,0.9)", borderRadius: 10, padding: "16px 22px", boxShadow: "0 8px 30px rgba(0,0,0,0.5)" }}>
      <div style={{ width: 6, height: 58, background: ACCENT, borderRadius: 3, marginRight: 18,
        transform: `scaleY(${seg(p, 0.2, 0.6)})`, transformOrigin: "center" }} />
      <div>
        <div style={{ color: TXT, fontFamily: FONT, fontWeight: 800, fontSize: 30, opacity: seg(p, 0.3, 0.7) }}>DADO-CHAVE</div>
        <div style={{ color: SUB, fontFamily: FONT, fontSize: 19, marginTop: 4, opacity: seg(p, 0.5, 0.9) }}>contexto · fonte</div>
      </div>
    </div>
  );
};

// ---- 2. Citação ----
const Quote: React.FC<{ p: number }> = ({ p }) => (
  <div style={{ opacity: seg(p, 0, 0.4), transform: `scale(${interpolate(seg(p, 0, 0.6), [0, 1], [0.9, 1])})`, textAlign: "center", maxWidth: 420 }}>
    <div style={{ color: ACCENT, fontFamily: "Georgia,serif", fontSize: 80, lineHeight: 0.5, height: 40 }}>“</div>
    <div style={{ color: TXT, fontFamily: "Georgia,serif", fontStyle: "italic", fontSize: 26, lineHeight: 1.4, opacity: seg(p, 0.3, 0.8) }}>
      A simplicidade é a máxima sofisticação.
    </div>
    <div style={{ color: SUB, fontFamily: FONT, fontSize: 18, marginTop: 12, opacity: seg(p, 0.6, 1) }}>— Autor</div>
  </div>
);

// ---- 3. Definição (caixa) ----
const Definition: React.FC<{ p: number }> = ({ p }) => (
  <div style={{ opacity: seg(p, 0, 0.4), maxWidth: 440 }}>
    <svg width={440} height={150} viewBox="0 0 440 150" style={{ position: "absolute" }}>
      <rect x={3} y={3} width={434} height={144} rx={12} fill="none" stroke={ACCENT2} strokeWidth={3}
        pathLength={1} strokeDasharray={1} strokeDashoffset={1 - seg(p, 0.15, 0.8)} />
    </svg>
    <div style={{ padding: "26px 28px", position: "relative" }}>
      <div style={{ color: ACCENT2, fontFamily: FONT, fontWeight: 800, fontSize: 26, opacity: seg(p, 0.25, 0.6) }}>Termo</div>
      <div style={{ color: SUB, fontFamily: FONT, fontSize: 19, lineHeight: 1.45, marginTop: 8, opacity: seg(p, 0.5, 0.9) }}>
        explicação curta e clara do conceito apresentado no roteiro.
      </div>
    </div>
  </div>
);

// ---- 4. Passos 1-2-3 ----
const Steps: React.FC<{ p: number }> = ({ p }) => {
  const xs = [60, 220, 380];
  const stepP = [seg(p, 0.05, 0.35), seg(p, 0.35, 0.6), seg(p, 0.6, 0.85)];
  const lineP = [seg(p, 0.3, 0.45), seg(p, 0.55, 0.7)];
  return (
    <svg width={440} height={150} viewBox="0 0 440 150">
      {lineP.map((lp, i) => (
        <line key={i} x1={xs[i] + 28} y1={55} x2={xs[i + 1] - 28} y2={55} stroke={ACCENT} strokeWidth={3}
          pathLength={1} strokeDasharray={1} strokeDashoffset={1 - lp} />
      ))}
      {xs.map((x, i) => (
        <g key={i} opacity={stepP[i]} transform={`translate(${x} 55) scale(${interpolate(stepP[i], [0, 1], [0.5, 1])})`}>
          <circle r={26} fill={i === 0 ? ACCENT : "rgba(251,191,36,0.15)"} stroke={ACCENT} strokeWidth={3} />
          <text y={9} fill={i === 0 ? "#0b1020" : ACCENT} fontSize={26} fontFamily={FONT} fontWeight={800} textAnchor="middle">{i + 1}</text>
          <text y={62} fill={SUB} fontSize={17} fontFamily={FONT} fontWeight={600} textAnchor="middle">Passo {i + 1}</text>
        </g>
      ))}
    </svg>
  );
};

// ---- 5. Antes -> Depois ----
const BeforeAfter: React.FC<{ p: number }> = ({ p }) => {
  const Panel = ({ x, lbl, color, pr }: { x: number; lbl: string; color: string; pr: number }) => (
    <g opacity={pr} transform={`translate(${x} 30) scale(${interpolate(pr, [0, 1], [0.85, 1])})`} style={{ transformOrigin: "center" }}>
      <rect width={150} height={92} rx={10} fill="rgba(255,255,255,0.05)" stroke={color} strokeWidth={2.5} />
      <text x={75} y={54} fill={color} fontSize={22} fontFamily={FONT} fontWeight={800} textAnchor="middle">{lbl}</text>
    </g>
  );
  return (
    <svg width={440} height={150} viewBox="0 0 440 150">
      <Panel x={20} lbl="Antes" color="#64748b" pr={seg(p, 0.1, 0.45)} />
      <g opacity={seg(p, 0.4, 0.7)}>
        <path d="M200 76 L 240 76" stroke={ACCENT} strokeWidth={4} strokeLinecap="round"
          pathLength={1} strokeDasharray={1} strokeDashoffset={1 - seg(p, 0.4, 0.7)} />
        <path d="M232 68 L 244 76 L 232 84" fill="none" stroke={ACCENT} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" opacity={seg(p, 0.6, 0.75)} />
      </g>
      <Panel x={270} lbl="Depois" color={ACCENT} pr={seg(p, 0.55, 0.9)} />
    </svg>
  );
};

// ---- 6. VS ----
const Versus: React.FC<{ p: number }> = ({ p }) => {
  const lx = interpolate(seg(p, 0, 0.5), [0, 1], [-60, 0]);
  const rx = interpolate(seg(p, 0, 0.5), [0, 1], [60, 0]);
  return (
    <div style={{ position: "relative", width: 440, height: 150 }}>
      <div style={{ position: "absolute", left: 0, top: 25, width: 200, height: 100, borderRadius: 10,
        background: "rgba(56,189,248,0.12)", border: `2px solid ${ACCENT2}`, transform: `translateX(${lx}px)`, opacity: seg(p, 0, 0.5),
        display: "flex", alignItems: "center", justifyContent: "center", color: ACCENT2, fontFamily: FONT, fontWeight: 800, fontSize: 26 }}>A</div>
      <div style={{ position: "absolute", right: 0, top: 25, width: 200, height: 100, borderRadius: 10,
        background: "rgba(251,191,36,0.12)", border: `2px solid ${ACCENT}`, transform: `translateX(${rx}px)`, opacity: seg(p, 0, 0.5),
        display: "flex", alignItems: "center", justifyContent: "center", color: ACCENT, fontFamily: FONT, fontWeight: 800, fontSize: 26 }}>B</div>
      <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(-50%,-50%) scale(${interpolate(seg(p, 0.45, 0.8), [0, 1], [0.4, 1])})`,
        opacity: seg(p, 0.45, 0.8), width: 64, height: 64, borderRadius: "50%", background: "#0b1020", border: `3px solid ${TXT}`,
        display: "flex", alignItems: "center", justifyContent: "center", color: TXT, fontFamily: FONT, fontWeight: 900, fontSize: 24 }}>VS</div>
    </div>
  );
};

const ITEMS: { nome: string; C: React.FC<{ p: number }> }[] = [
  { nome: "Lower-third (fato)", C: LowerThird },
  { nome: "Citação", C: Quote },
  { nome: "Definição", C: Definition },
  { nome: "Passos 1-2-3", C: Steps },
  { nome: "Antes → Depois", C: BeforeAfter },
  { nome: "VS (comparação)", C: Versus },
];

const Cell: React.FC<{ item: typeof ITEMS[0]; idx: number }> = ({ item, idx }) => {
  const frame = useCurrentFrame();
  const local = (frame + idx * 5) % LOOP;
  const p = interpolate(local, [10, 80], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const fade = interpolate(local, [0, 8, LOOP - 16, LOOP - 2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const C = item.C;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14, opacity: fade, padding: 16 }}>
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}><C p={p} /></div>
      <div style={{ color: SUB, fontFamily: FONT, fontSize: 22, marginTop: 4 }}>{item.nome}</div>
    </div>
  );
};

export const CardsStructure: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0e1626 0%, #05070d 100%)", padding: 50 }}>
      <div style={{ color: "#fff", fontFamily: FONT, fontWeight: 700, fontSize: 40, textAlign: "center", marginBottom: 26 }}>
        Cards & estrutura — organizam a explicação
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gridTemplateRows: "repeat(2, 1fr)", gap: 22, height: H - 180 }}>
        {ITEMS.map((it, i) => <Cell key={i} item={it} idx={i} />)}
      </div>
    </AbsoluteFill>
  );
};
