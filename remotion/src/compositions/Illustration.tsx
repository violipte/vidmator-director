import React from "react";
import { AbsoluteFill, interpolate, Easing, useCurrentFrame } from "remotion";
import { ICON_RENDERERS } from "./AnimatedIcons";

// Renderiza UM elemento ilustrativo a partir de um spec preenchido pelo LLM.
// Usado como overlay por cena no BrollTest (camada de texto, nítido).
// DEFENSIVO: o LLM gera shapes imprevisíveis (valor pode ser texto, a/b pode ser objeto) ->
// txt()/num() coagem com segurança e <Safe> (ErrorBoundary) impede que um spec ruim mate o render.

const ACCENT = "#fbbf24";
const ACCENT2 = "#38bdf8";
const TXT = "#eef4fc";
const SUB = "#aab6c6";
const FONT = "'Segoe UI',system-ui,sans-serif";

export type IlustracaoSpec = {
  tipo: "icone" | "grafico" | "card";
  pos?: "left" | "right" | "center" | "lower";
  tamanho?: "grande" | "medio"; // default grande (chamativo)
  nome?: string;
  legenda?: string;
  chart?: "bar" | "line" | "donut" | "stat" | "comparison" | "progress";
  dados?: any;
  variante?: "lowerthird" | "quote" | "definition" | "steps" | "beforeafter" | "vs";
  conteudo?: any;
};

// ---------- coerção segura (nunca renderiza objeto cru nem NaN) ----------
const txt = (v: any, fb = ""): string => {
  if (v == null) return fb;
  if (typeof v === "string") return v;
  if (typeof v === "number") return Number.isFinite(v) ? String(v) : fb;
  if (typeof v === "object") {
    const lab = v.label ?? v.titulo ?? v.texto ?? v.termo ?? v.nome ?? v.title;
    const val = v.valor ?? v.value;
    if (lab != null && val != null && typeof val !== "object") return `${txt(lab)} ${txt(val)}`.trim();
    if (lab != null) return txt(lab);
    return fb;
  }
  return String(v);
};
const num = (v: any, fb = 0): number => {
  if (typeof v === "number") return Number.isFinite(v) ? v : fb;
  if (typeof v === "string") { const m = parseFloat(v.replace(/[^0-9.\-]/g, "")); return Number.isFinite(m) ? m : fb; }
  if (v && typeof v === "object") return num(v.valor ?? v.value, fb);
  return fb;
};
const asList = (v: any): any[] => (Array.isArray(v) ? v : []);

// ErrorBoundary: spec inesperado do LLM -> renderiza nada (não derruba o render inteiro).
export class Safe extends React.Component<{ children: React.ReactNode }, { err: boolean }> {
  state = { err: false };
  static getDerivedStateFromError() { return { err: true }; }
  render() { return this.state.err ? null : this.props.children; }
}

const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));
const dashP = (p: number) => ({ pathLength: 1, strokeDasharray: 1, strokeDashoffset: 1 - p } as any);

// ---------- GRÁFICOS (parametrizados) ----------
const ChartBar: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const raw = asList(d?.valores);
  const vals = (raw.length ? raw : [{ valor: 40 }, { valor: 72 }, { valor: 55 }, { valor: 90 }])
    .map((v: any) => ({ label: txt(typeof v === "object" ? v?.label : ""), valor: num(typeof v === "object" ? v?.valor : v) }));
  const destaque = num(d?.destaque, vals.length - 1);
  const max = Math.max(...vals.map((v) => v.valor), 1);
  const W = 420, gap = 20, bw = Math.min(70, (W - 60 - gap * (vals.length - 1)) / Math.max(vals.length, 1));
  return (
    <svg width={W} height={300} viewBox={`0 0 ${W} 300`}>
      <line x1={30} y1={250} x2={W - 20} y2={250} stroke="#334155" strokeWidth={3} />
      {vals.map((v, i) => {
        const hh = 190 * (v.valor / max) * p;
        const x = 40 + i * (bw + gap);
        return (
          <g key={i}>
            <rect x={x} y={250 - hh} width={bw} height={hh} rx={6} fill={i === destaque ? ACCENT : ACCENT2} />
            <text x={x + bw / 2} y={244 - hh} fill={TXT} fontSize={26} fontFamily={FONT} fontWeight={800} textAnchor="middle">{Math.round(v.valor * p)}</text>
            {v.label && <text x={x + bw / 2} y={278} fill={SUB} fontSize={20} fontFamily={FONT} textAnchor="middle">{v.label}</text>}
          </g>
        );
      })}
    </svg>
  );
};

const ChartLine: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const raw = asList(d?.valores).map((y) => num(y));
  const ys: number[] = raw.length ? raw : [20, 45, 35, 70, 60, 95];
  const W = 460, Hh = 280, pad = 40;
  const max = Math.max(...ys, 1), min = Math.min(...ys, 0);
  const pts = ys.map((y, i) => [pad + (i * (W - 2 * pad)) / Math.max(ys.length - 1, 1), Hh - pad - ((y - min) / (max - min || 1)) * (Hh - 2 * pad)]);
  const dPath = "M" + pts.map((q) => `${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(" L ");
  const last = pts[pts.length - 1];
  return (
    <svg width={W} height={Hh} viewBox={`0 0 ${W} ${Hh}`}>
      <path d={`${dPath} L ${last[0]} ${Hh - pad} L ${pad} ${Hh - pad} Z`} fill={ACCENT2} opacity={0.13 * p} />
      <path d={dPath} fill="none" stroke={ACCENT2} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" {...dashP(p)} />
      {p > 0.92 && <circle cx={last[0]} cy={last[1]} r={8} fill={ACCENT} />}
    </svg>
  );
};

const ChartDonut: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const target = num(d?.valor, 73);
  const r = 78, cx = 120, cy = 120;
  const label = txt(d?.label);
  return (
    <svg width={240} height={240} viewBox="0 0 240 240">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e293b" strokeWidth={20} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={ACCENT} strokeWidth={20} strokeLinecap="round" {...dashP((target / 100) * p)} transform={`rotate(-90 ${cx} ${cy})`} />
      <text x={cx} y={cy + 14} fill={TXT} fontSize={52} fontFamily={FONT} fontWeight={800} textAnchor="middle">{Math.round(target * p)}%</text>
      {label && <text x={cx} y={cy + 48} fill={SUB} fontSize={20} fontFamily={FONT} textAnchor="middle">{label}</text>}
    </svg>
  );
};

const ChartStat: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const valor = num(d?.valor, 2.4), suf = txt(d?.sufixo, "M"), dec = valor % 1 !== 0 ? 1 : 0;
  const label = txt(d?.label);
  return (
    <svg width={420} height={230} viewBox="0 0 420 230">
      <text x={210} y={120} fill={ACCENT} fontSize={108} fontFamily={FONT} fontWeight={800} textAnchor="middle">{(valor * p).toFixed(dec)}{suf}</text>
      <line x1={120} y1={150} x2={300} y2={150} stroke={ACCENT} strokeWidth={5} strokeLinecap="round" {...dashP(p)} />
      {label && <text x={210} y={195} fill={SUB} fontSize={26} fontFamily={FONT} fontWeight={600} textAnchor="middle">{label}</text>}
    </svg>
  );
};

// comparison: aceita a/b numérico (barras) OU TEXTO (dicotomia). Se nenhum lado tem número
// real, vira COMPARAÇÃO DE TEXTO (2 colunas com label + detalhe) — ex.: dicotomia estoica.
const _hasNum = (v: any): boolean =>
  typeof v === "number" ? Number.isFinite(v)
    : typeof v === "string" ? /[0-9]/.test(v)
    : !!v && typeof v === "object" ? /[0-9]/.test(String(v.valor ?? v.value ?? "")) : false;

const ChartComparison: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const A = d?.a, B = d?.b;
  if (!_hasNum(A) && !_hasNum(B)) {
    // comparação de TEXTO
    const col = (v: any, color: string) => {
      const head = txt(typeof v === "object" ? (v?.label ?? v?.titulo) : v, "—");
      const body = typeof v === "object" ? txt(v?.valor ?? v?.texto ?? v?.sub) : "";
      return (
        <div style={{ flex: 1, background: "rgba(8,14,24,0.86)", border: `3px solid ${color}`, borderRadius: 14, padding: "20px 22px" }}>
          <div style={{ color, fontFamily: FONT, fontWeight: 800, fontSize: 28 }}>{head}</div>
          {body && <div style={{ color: TXT, fontFamily: FONT, fontSize: 22, marginTop: 8, lineHeight: 1.35 }}>{body}</div>}
        </div>
      );
    };
    return (
      <div style={{ display: "flex", gap: 18, width: 640, opacity: seg(p, 0.1, 0.6), transform: `translateY(${(1 - seg(p, 0, 0.5)) * 16}px)` }}>
        {col(A ?? { label: "A" }, "#64748b")}{col(B ?? { label: "B" }, ACCENT)}
      </div>
    );
  }
  const a = { label: txt(typeof A === "object" ? A?.label : A, "Antes"), valor: num(A, 42) };
  const b = { label: txt(typeof B === "object" ? B?.label : B, "Depois"), valor: num(B, 88) };
  const max = Math.max(a.valor, b.valor, 1);
  const row = (rw: any, y: number, c: string) => {
    const full = 300 * (rw.valor / max);
    return (
      <g>
        <text x={20} y={y - 12} fill={TXT} fontSize={24} fontFamily={FONT} fontWeight={700}>{rw.label}</text>
        <rect x={20} y={y} width={320} height={32} rx={16} fill="#1e293b" />
        <rect x={20} y={y} width={full * p} height={32} rx={16} fill={c} />
        <text x={350} y={y + 26} fill={TXT} fontSize={24} fontFamily={FONT} fontWeight={700}>{Math.round(rw.valor * p)}</text>
      </g>
    );
  };
  return (
    <svg width={420} height={210} viewBox="0 0 420 210">
      {row(a, 60, "#64748b")}
      {row(b, 140, ACCENT)}
    </svg>
  );
};

const ChartProgress: React.FC<{ p: number; d: any }> = ({ p, d }) => {
  const target = num(d?.valor, 68);
  return (
    <svg width={420} height={140} viewBox="0 0 420 140">
      <text x={20} y={56} fill={TXT} fontSize={28} fontFamily={FONT} fontWeight={700}>{txt(d?.label, "Progresso")}</text>
      <text x={400} y={56} fill={ACCENT} fontSize={28} fontFamily={FONT} fontWeight={800} textAnchor="end">{Math.round(target * p)}%</text>
      <rect x={20} y={76} width={380} height={26} rx={13} fill="#1e293b" />
      <rect x={20} y={76} width={380 * (target / 100) * p} height={26} rx={13} fill={ACCENT} />
    </svg>
  );
};

const CHARTS: Record<string, React.FC<{ p: number; d: any }>> = {
  bar: ChartBar, line: ChartLine, donut: ChartDonut, stat: ChartStat, comparison: ChartComparison, progress: ChartProgress,
};

// ---------- CARDS (parametrizados) ----------
const CardLowerThird: React.FC<{ p: number; c: any }> = ({ p, c }) => (
  <div style={{ display: "flex", alignItems: "center", background: "rgba(8,14,24,0.9)", borderRadius: 12, padding: "20px 28px", boxShadow: "0 10px 36px rgba(0,0,0,0.55)" }}>
    <div style={{ width: 7, height: 64, background: ACCENT, borderRadius: 4, marginRight: 22, transform: `scaleY(${seg(p, 0.1, 0.5)})` }} />
    <div>
      <div style={{ color: TXT, fontFamily: FONT, fontWeight: 800, fontSize: 38, opacity: seg(p, 0.25, 0.6) }}>{txt(c?.titulo, "Dado-chave")}</div>
      {c?.sub && <div style={{ color: SUB, fontFamily: FONT, fontSize: 24, marginTop: 5, opacity: seg(p, 0.5, 0.9) }}>{txt(c.sub)}</div>}
    </div>
  </div>
);

const CardQuote: React.FC<{ p: number; c: any }> = ({ p, c }) => (
  <div style={{ textAlign: "center", maxWidth: 760, transform: `scale(${interpolate(seg(p, 0, 0.5), [0, 1], [0.92, 1])})` }}>
    <div style={{ color: ACCENT, fontFamily: "Georgia,serif", fontSize: 96, lineHeight: 0.5, height: 50 }}>“</div>
    <div style={{ color: TXT, fontFamily: "Georgia,serif", fontStyle: "italic", fontSize: 38, lineHeight: 1.4, opacity: seg(p, 0.3, 0.8) }}>{txt(c?.texto)}</div>
    {c?.autor && <div style={{ color: SUB, fontFamily: FONT, fontSize: 24, marginTop: 16, opacity: seg(p, 0.6, 1) }}>— {txt(c.autor)}</div>}
  </div>
);

const CardDefinition: React.FC<{ p: number; c: any }> = ({ p, c }) => (
  <div style={{ maxWidth: 700, position: "relative" }}>
    <svg width={700} height={200} viewBox="0 0 700 200" style={{ position: "absolute" }} preserveAspectRatio="none">
      <rect x={3} y={3} width={694} height={194} rx={14} fill="rgba(8,14,24,0.78)" stroke={ACCENT2} strokeWidth={3} {...dashP(seg(p, 0.15, 0.8))} />
    </svg>
    <div style={{ padding: "32px 38px", position: "relative" }}>
      <div style={{ color: ACCENT2, fontFamily: FONT, fontWeight: 800, fontSize: 34, opacity: seg(p, 0.25, 0.6) }}>{txt(c?.termo, "Termo")}</div>
      <div style={{ color: TXT, fontFamily: FONT, fontSize: 26, lineHeight: 1.45, marginTop: 10, opacity: seg(p, 0.5, 0.9) }}>{txt(c?.texto)}</div>
    </div>
  </div>
);

// quebra um label em linhas curtas (~max chars/linha), até 3 linhas — evita sobreposição entre colunas
const wrapLbl = (s: string, max = 16): string[] => {
  const lines: string[] = []; let cur = "";
  for (const w of String(s).split(/\s+/)) {
    if (cur && (cur + " " + w).length > max) { lines.push(cur); cur = w; }
    else cur = (cur ? cur + " " + w : w);
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 3);
};

const CardSteps: React.FC<{ p: number; c: any }> = ({ p, c }) => {
  const passos: string[] = asList(c?.passos).map((s) => txt(s)).filter(Boolean).slice(0, 4);
  const list = passos.length ? passos : ["Step 1", "Step 2", "Step 3"];
  const n = list.length, COL = 260, W = 100 + (n - 1) * COL + 100, H = 210;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      {list.slice(0, -1).map((_, i) => {
        const x1 = 100 + i * COL, x2 = 100 + (i + 1) * COL;
        return <line key={i} x1={x1 + 32} y1={55} x2={x2 - 32} y2={55} stroke={ACCENT} strokeWidth={4} {...dashP(seg(p, 0.3 + i * 0.2, 0.45 + i * 0.2))} />;
      })}
      {list.map((lbl, i) => {
        const x = 100 + i * COL, sp = seg(p, 0.05 + i * 0.22, 0.3 + i * 0.22);
        const lines = wrapLbl(lbl, 16);
        return (
          <g key={i} opacity={sp} transform={`translate(${x} 55) scale(${interpolate(sp, [0, 1], [0.5, 1])})`}>
            <circle r={30} fill={i === 0 ? ACCENT : "rgba(251,191,36,0.16)"} stroke={ACCENT} strokeWidth={3} />
            <text y={11} fill={i === 0 ? "#0b1020" : ACCENT} fontSize={30} fontFamily={FONT} fontWeight={800} textAnchor="middle">{i + 1}</text>
            <text y={70} fill={TXT} fontSize={21} fontFamily={FONT} fontWeight={600} textAnchor="middle">
              {lines.map((ln, j) => <tspan key={j} x={0} dy={j === 0 ? 0 : 25}>{ln}</tspan>)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

const CardBeforeAfter: React.FC<{ p: number; c: any }> = ({ p, c }) => {
  const Panel = ({ x, lbl, color, pr }: any) => (
    <g opacity={pr} transform={`translate(${x} 30)`}>
      <rect width={220} height={120} rx={12} fill="rgba(255,255,255,0.05)" stroke={color} strokeWidth={3} />
      <text x={110} y={70} fill={color} fontSize={30} fontFamily={FONT} fontWeight={800} textAnchor="middle">{lbl}</text>
    </g>
  );
  return (
    <svg width={620} height={180} viewBox="0 0 620 180">
      <Panel x={20} lbl={txt(c?.antes, "Antes")} color="#64748b" pr={seg(p, 0.1, 0.45)} />
      <g opacity={seg(p, 0.4, 0.7)}>
        <path d="M280 90 L 330 90" stroke={ACCENT} strokeWidth={5} strokeLinecap="round" {...dashP(seg(p, 0.4, 0.7))} />
        <path d="M320 80 L 334 90 L 320 100" fill="none" stroke={ACCENT} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" opacity={seg(p, 0.6, 0.8)} />
      </g>
      <Panel x={380} lbl={txt(c?.depois, "Depois")} color={ACCENT} pr={seg(p, 0.55, 0.9)} />
    </svg>
  );
};

// vs: cada lado pode ser STRING ou {label, valor} -> mostra título (label) + detalhe (valor).
const CardVs: React.FC<{ p: number; c: any }> = ({ p, c }) => {
  const lx = interpolate(seg(p, 0, 0.5), [0, 1], [-70, 0]);
  const rx = interpolate(seg(p, 0, 0.5), [0, 1], [70, 0]);
  const part = (v: any, fbHead: string) => ({
    head: txt(typeof v === "object" ? (v?.label ?? v?.titulo) : v, fbHead),
    sub: typeof v === "object" ? txt(v?.valor ?? v?.texto ?? v?.sub) : "",
  });
  const A = part(c?.a, "A"), B = part(c?.b, "B");
  const box = (side: "l" | "r", d: { head: string; sub: string }, color: string, tx: number) => (
    <div style={{ position: "absolute", [side === "l" ? "left" : "right"]: 0, top: 20, width: 300, minHeight: 150, borderRadius: 12,
      background: side === "l" ? "rgba(56,189,248,0.12)" : "rgba(251,191,36,0.12)", border: `3px solid ${color}`,
      transform: `translateX(${tx}px)`, opacity: seg(p, 0, 0.5), display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", padding: "16px 18px", textAlign: "center" }}>
      <div style={{ color, fontFamily: FONT, fontWeight: 800, fontSize: 30 }}>{d.head}</div>
      {d.sub && <div style={{ color: TXT, fontFamily: FONT, fontSize: 22, marginTop: 8, lineHeight: 1.3 }}>{d.sub}</div>}
    </div>
  );
  return (
    <div style={{ position: "relative", width: 680, height: 210 }}>
      {box("l", A, ACCENT2, lx)}
      {box("r", B, ACCENT, rx)}
      <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(-50%,-50%) scale(${interpolate(seg(p, 0.45, 0.8), [0, 1], [0.4, 1])})`,
        opacity: seg(p, 0.45, 0.8), width: 76, height: 76, borderRadius: "50%", background: "#0b1020", border: `4px solid ${TXT}`,
        display: "flex", alignItems: "center", justifyContent: "center", color: TXT, fontFamily: FONT, fontWeight: 900, fontSize: 28, zIndex: 2 }}>VS</div>
    </div>
  );
};

const CARDS: Record<string, React.FC<{ p: number; c: any }>> = {
  lowerthird: CardLowerThird, quote: CardQuote, definition: CardDefinition, steps: CardSteps, beforeafter: CardBeforeAfter, vs: CardVs,
};

// ---------- POSICIONAMENTO ----------
const posStyle = (pos: string): React.CSSProperties => {
  switch (pos) {
    case "left": return { justifyContent: "center", alignItems: "flex-start", paddingLeft: 130 };
    case "right": return { justifyContent: "center", alignItems: "flex-end", paddingRight: 130 };
    case "lower": return { justifyContent: "flex-end", alignItems: "center", paddingBottom: 150 };
    default: return { justifyContent: "center", alignItems: "center" };
  }
};

export const Illustration: React.FC<{ spec: IlustracaoSpec; sceneFrames: number }> = ({ spec, sceneFrames }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [6, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const entr = interpolate(frame, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exit = interpolate(frame, [sceneFrames - 12, sceneFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const opacity = Math.min(entr, exit);
  const pos = spec.pos || (spec.tipo === "card" && spec.variante === "lowerthird" ? "lower" : "center");

  let el: React.ReactNode = null;
  if (spec.tipo === "icone") {
    const r = ICON_RENDERERS[spec.nome || "ideia"] || ICON_RENDERERS.ideia;
    el = (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", color: "#e9eef7" }}>
        <svg width={300} height={300} viewBox="0 0 120 120" style={{ filter: "drop-shadow(0 4px 18px rgba(0,0,0,0.6))" }}>{r(p)}</svg>
        {spec.legenda && <div style={{ color: TXT, fontFamily: FONT, fontWeight: 700, fontSize: 36, marginTop: 8, textShadow: "0 2px 12px rgba(0,0,0,0.9)" }}>{txt(spec.legenda)}</div>}
      </div>
    );
  } else if (spec.tipo === "grafico") {
    const C = CHARTS[spec.chart || "bar"] || ChartBar;
    el = <div style={{ filter: "drop-shadow(0 6px 22px rgba(0,0,0,0.55))" }}><C p={p} d={spec.dados} /></div>;
  } else if (spec.tipo === "card") {
    const C = CARDS[spec.variante || "lowerthird"] || CardLowerThird;
    el = <C p={p} c={spec.conteudo} />;
  }

  // GRANDE por padrão (chama atenção). LLM pode pedir "medio".
  const baseBig: Record<string, number> = { grafico: 1.8, card: 1.45, icone: 1.6 };
  let scale = (baseBig[spec.tipo] || 1.4) * (spec.tamanho === "medio" ? 0.68 : 1);
  if (spec.tipo === "card" && spec.variante === "lowerthird") scale *= 0.92; // já é largo
  const origin = pos === "lower" ? "center bottom" : pos === "left" ? "left center" : pos === "right" ? "right center" : "center center";

  return (
    <AbsoluteFill style={{ display: "flex", flexDirection: "column", ...posStyle(pos), opacity }}>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, rgba(0,0,0,0.42) 0%, transparent 64%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", transform: `scale(${scale})`, transformOrigin: origin }}><Safe>{el}</Safe></div>
    </AbsoluteFill>
  );
};
