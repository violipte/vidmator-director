import { AbsoluteFill, interpolate, Easing, useCurrentFrame } from "remotion";

// Dados & gráficos animados — pra ilustrar estatísticas/comparações do roteiro (qualquer nicho).

const ACCENT = "#fbbf24";
const ACCENT2 = "#38bdf8";
const TXT = "#e9eef7";
const H = 1080;
const LOOP = 140;
const FONT = "'Segoe UI',system-ui,sans-serif";

const useP = (idx: number) => {
  const frame = useCurrentFrame();
  const local = (frame + idx * 4) % LOOP;
  const p = interpolate(local, [10, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const fade = interpolate(local, [0, 8, LOOP - 14, LOOP - 2], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return { p, fade };
};

const BarChart: React.FC<{ p: number }> = ({ p }) => {
  const bars = [{ h: 0.45, v: 40 }, { h: 0.72, v: 72 }, { h: 0.58, v: 55 }, { h: 1.0, v: 90 }];
  return (
    <svg width={300} height={200} viewBox="0 0 300 200">
      <line x1={30} y1={170} x2={285} y2={170} stroke="#334155" strokeWidth={2} />
      {bars.map((b, i) => {
        const full = 130 * b.h;
        const hh = full * p;
        const x = 50 + i * 60;
        return (
          <g key={i}>
            <rect x={x} y={170 - hh} width={38} height={hh} rx={5} fill={i === 3 ? ACCENT : ACCENT2} opacity={0.92} />
            <text x={x + 19} y={165 - hh} fill={TXT} fontSize={18} fontFamily={FONT} fontWeight={700} textAnchor="middle">
              {Math.round(b.v * p)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

const LineGraph: React.FC<{ p: number }> = ({ p }) => {
  const pts = [[30, 150], [80, 120], [130, 135], [180, 80], [230, 95], [280, 40]];
  const d = "M" + pts.map((q) => q.join(" ")).join(" L ");
  const last = pts[pts.length - 1];
  const area = `${d} L ${last[0]} 170 L 30 170 Z`;
  return (
    <svg width={310} height={200} viewBox="0 0 310 200">
      <path d={area} fill={ACCENT2} opacity={0.12 * p} />
      <path d={d} fill="none" stroke={ACCENT2} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round"
        pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
      {p > 0.9 && <circle cx={last[0]} cy={last[1]} r={6} fill={ACCENT} />}
    </svg>
  );
};

const Donut: React.FC<{ p: number; target?: number }> = ({ p, target = 73 }) => {
  const r = 64, cx = 100, cy = 100;
  const frac = (target / 100) * p;
  return (
    <svg width={200} height={200} viewBox="0 0 200 200">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e293b" strokeWidth={16} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={ACCENT} strokeWidth={16} strokeLinecap="round"
        pathLength={1} strokeDasharray={1} strokeDashoffset={1 - frac} transform={`rotate(-90 ${cx} ${cy})`} />
      <text x={cx} y={cy + 12} fill={TXT} fontSize={42} fontFamily={FONT} fontWeight={800} textAnchor="middle">
        {Math.round(target * p)}%
      </text>
    </svg>
  );
};

const BigStat: React.FC<{ p: number }> = ({ p }) => (
  <svg width={300} height={200} viewBox="0 0 300 200">
    <text x={150} y={110} fill={ACCENT} fontSize={86} fontFamily={FONT} fontWeight={800} textAnchor="middle">
      {(2.4 * p).toFixed(1)}M
    </text>
    <line x1={90} y1={130} x2={210} y2={130} stroke={ACCENT} strokeWidth={4} strokeLinecap="round"
      pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
    <text x={150} y={162} fill="#9aa7b8" fontSize={22} fontFamily={FONT} fontWeight={600} textAnchor="middle">
      pessoas alcançadas
    </text>
  </svg>
);

const Comparison: React.FC<{ p: number }> = ({ p }) => {
  const rows = [{ lbl: "Antes", w: 0.42, v: 42, c: "#64748b" }, { lbl: "Depois", w: 0.88, v: 88, c: ACCENT }];
  return (
    <svg width={300} height={200} viewBox="0 0 300 200">
      {rows.map((rw, i) => {
        const y = 60 + i * 70;
        const full = 200 * rw.w;
        return (
          <g key={i}>
            <text x={20} y={y - 12} fill={TXT} fontSize={20} fontFamily={FONT} fontWeight={700}>{rw.lbl}</text>
            <rect x={20} y={y} width={210} height={26} rx={13} fill="#1e293b" />
            <rect x={20} y={y} width={full * p} height={26} rx={13} fill={rw.c} />
            <text x={235} y={y + 21} fill={TXT} fontSize={20} fontFamily={FONT} fontWeight={700}>{Math.round(rw.v * p)}%</text>
          </g>
        );
      })}
    </svg>
  );
};

const Progress: React.FC<{ p: number; target?: number }> = ({ p, target = 68 }) => (
  <svg width={300} height={200} viewBox="0 0 300 200">
    <text x={30} y={80} fill={TXT} fontSize={24} fontFamily={FONT} fontWeight={700}>Progresso</text>
    <text x={270} y={80} fill={ACCENT} fontSize={24} fontFamily={FONT} fontWeight={800} textAnchor="end">{Math.round(target * p)}%</text>
    <rect x={30} y={100} width={240} height={20} rx={10} fill="#1e293b" />
    <rect x={30} y={100} width={240 * (target / 100) * p} height={20} rx={10} fill={ACCENT} />
  </svg>
);

const CHARTS: { nome: string; C: React.FC<{ p: number }> }[] = [
  { nome: "Barras", C: BarChart },
  { nome: "Linha (tendência)", C: LineGraph },
  { nome: "Donut %", C: Donut },
  { nome: "Stat grande", C: BigStat },
  { nome: "Comparação", C: Comparison },
  { nome: "Barra de progresso", C: Progress },
];

const Cell: React.FC<{ item: typeof CHARTS[0]; idx: number }> = ({ item, idx }) => {
  const { p, fade } = useP(idx);
  const C = item.C;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 14, opacity: fade }}>
      <C p={p} />
      <div style={{ color: "#9aa7b8", fontFamily: FONT, fontSize: 22, marginTop: 4 }}>{item.nome}</div>
    </div>
  );
};

export const DataViz: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0e1626 0%, #05070d 100%)", padding: 50 }}>
      <div style={{ color: "#fff", fontFamily: FONT, fontWeight: 700, fontSize: 40, textAlign: "center", marginBottom: 26 }}>
        Dados & gráficos — ilustram estatísticas do roteiro
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gridTemplateRows: "repeat(2, 1fr)", gap: 22, height: H - 180 }}>
        {CHARTS.map((c, i) => <Cell key={i} item={c} idx={i} />)}
      </div>
    </AbsoluteFill>
  );
};
