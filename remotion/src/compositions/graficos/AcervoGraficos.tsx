import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO DE GRÁFICOS — 10 variações (2026-07-20).
   CONTRATO ÚNICO: { title, kicker?, accent?, labels?: string[],
   values?: number[], suffix? }  — cada variação interpreta:
   contador usa values[0]; percent usa values[0] como %; versus usa
   [0] vs [1]; tendência/rank usam a série completa + labels.
   ============================================================ */

type P = { title?: string; kicker?: string; accent?: string; labels?: string[]; values?: number[]; suffix?: string };
const DISPLAY = F_DISPLAY;
const MONO = F_MONO;
const SANS = F_SANS;
const BG = "#0a0b0f";

const Kicker: React.FC<{ k?: string; accent: string; op?: number }> = ({ k, accent, op = 1 }) =>
  k ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 25, color: accent, letterSpacing: 8, marginBottom: 26, opacity: op, textAlign: "center" }}>{k.toUpperCase()}</div> : null;

const fmt = (v: number) => (v % 1 === 0 ? v.toLocaleString("en-US") : v.toFixed(1));

/* 01 COUNTER GLOW — número gigante contando com glow + título */
export const Graf01_CounterGlow: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "" }) => {
  const f = useCurrentFrame();
  const alvo = values[0] ?? 0;
  {/* assenta em ~0.9s: QA tenis 23/07 — contagem lenta flagrada no meio ("3" de 5, "18" de 25) */}
  const v = interpolate(f, [4, 26], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 85% at 50% 46%, #12151c 0%, ${BG} 78%)`, justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 190, color: "#f5f2ea", lineHeight: 1, textShadow: `0 0 70px ${accent}88, 0 0 24px ${accent}55`, opacity: op }}>
        {fmt(v)}{suffix}
      </div>
      <div style={{ fontFamily: DISPLAY, fontSize: 40, color: accent, letterSpacing: 5, marginTop: 26, opacity: op, textTransform: "uppercase" }}>{title}</div>
    </AbsoluteFill>
  );
};

/* 02 ODOMETER — dígitos rolando estilo hodômetro mecânico (vibe automotiva) */
export const Graf02_Odometer: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "" }) => {
  const f = useCurrentFrame();
  const alvo = Math.round(values[0] ?? 0);
  const alvoStr = alvo.toLocaleString("en-US");
  const prog = interpolate(f, [4, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.quad) });
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#0d0e10", justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ display: "flex", gap: 10, opacity: op }}>
        {alvoStr.split("").map((ch, i) => {
          if (ch === ",") return <div key={i} style={{ fontFamily: MONO, fontSize: 120, color: accent, alignSelf: "flex-end" }}>,</div>;
          const dig = parseInt(ch);
          const atual = Math.floor(dig * Math.min(1, prog + (alvoStr.length - i) * 0.04 * (1 - prog)));
          const rolando = prog < 1 ? (atual + Math.floor(f / 2 + i)) % 10 : dig;
          const mostra = prog > 0.85 ? dig : rolando;
          return (
            <div key={i} style={{ width: 108, height: 168, background: "linear-gradient(180deg, #1a1c20 0%, #111317 45%, #1a1c20 100%)", border: "1px solid rgba(255,255,255,0.14)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "inset 0 8px 18px rgba(0,0,0,0.7), 0 10px 30px rgba(0,0,0,0.5)" }}>
              <span style={{ fontFamily: MONO, fontSize: 118, fontWeight: 700, color: "#efe9dc" }}>{mostra}</span>
            </div>
          );
        })}
        {suffix ? <div style={{ fontFamily: DISPLAY, fontSize: 110, color: accent, alignSelf: "center", marginLeft: 14 }}>{suffix}</div> : null}
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 38, color: "#cfd3da", letterSpacing: 4, marginTop: 34, opacity: op, textTransform: "uppercase" }}>{title}</div>
    </AbsoluteFill>
  );
};

/* 03 DONUT PERCENT — anel de progresso com % central */
export const Graf03_DonutPercent: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0] }) => {
  const f = useCurrentFrame();
  const alvo = Math.min(100, values[0] ?? 0);
  const v = interpolate(f, [4, 26], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const R = 240, C = 2 * Math.PI * R;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 80% at 50% 50%, #12141a 0%, ${BG} 80%)`, justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ position: "relative", width: 560, height: 560, opacity: op }}>
        <svg width={560} height={560} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={280} cy={280} r={R} fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth={44} />
          <circle cx={280} cy={280} r={R} fill="none" stroke={accent} strokeWidth={44} strokeLinecap="round"
            strokeDasharray={C} strokeDashoffset={C * (1 - v / 100)} style={{ filter: `drop-shadow(0 0 22px ${accent}aa)` }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 130, color: "#fff", lineHeight: 1 }}>{Math.round(v)}%</span>
        </div>
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, color: "#d7dae0", marginTop: 30, opacity: op, maxWidth: 900, textAlign: "center" }}>{title}</div>
    </AbsoluteFill>
  );
};

/* 04 GAUGE METER — velocímetro/manômetro com ponteiro (automotivo) */
export const Graf04_GaugeMeter: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "%" }) => {
  const f = useCurrentFrame();
  const alvo = Math.min(100, values[0] ?? 0);
  const v = interpolate(f, [6, 48], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const ang = -120 + (v / 100) * 240;
  return (
    <AbsoluteFill style={{ background: "#0c0d10", justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ position: "relative", width: 640, height: 420, opacity: op }}>
        <svg width={640} height={420} viewBox="0 0 640 420">
          {Array.from({ length: 25 }).map((_, i) => {
            const a = (-120 + i * 10) * (Math.PI / 180);
            const on = (-120 + i * 10) <= ang;
            const x1 = 320 + Math.sin(a) * 250, y1 = 330 - Math.cos(a) * 250;
            const x2 = 320 + Math.sin(a) * (i % 5 === 0 ? 200 : 222), y2 = 330 - Math.cos(a) * (i % 5 === 0 ? 200 : 222);
            return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={on ? accent : "rgba(255,255,255,0.18)"} strokeWidth={i % 5 === 0 ? 8 : 4} strokeLinecap="round" style={on ? { filter: `drop-shadow(0 0 6px ${accent})` } : undefined} />;
          })}
          <g transform={`rotate(${ang} 320 330)`}>
            <line x1={320} y1={330} x2={320} y2={130} stroke="#f2efe8" strokeWidth={10} strokeLinecap="round" style={{ filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.8))" }} />
          </g>
          <circle cx={320} cy={330} r={26} fill="#1a1c20" stroke={accent} strokeWidth={5} />
        </svg>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: -16, textAlign: "center", fontFamily: DISPLAY, fontSize: 84, color: "#fff" }}>{Math.round(v)}{suffix}</div>
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, color: "#d7dae0", marginTop: 46, opacity: op, textTransform: "uppercase", letterSpacing: 3 }}>{title}</div>
    </AbsoluteFill>
  );
};

/* 05 VERSUS BARS — A vs B em barras verticais dark (redesign) */
export const Graf05_VersusBars: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = ["A", "B"], values = [0, 0], suffix = "%" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const max = Math.max(values[0] ?? 1, values[1] ?? 1, 1);
  return (
    /* VidRush 24/07: chart COMPARATIVO = card CLARO (creme, grid caderno) */
    <AbsoluteFill style={{ background: "#f2eee2", justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px), repeating-linear-gradient(90deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px)" }} />
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 52, color: "#241f16", marginBottom: 84, opacity: op }}>{title}</div>
      <div style={{ display: "flex", gap: 170, alignItems: "flex-end", height: 470 }}>
        {[0, 1].map((i) => {
          const alvo = values[i] ?? 0;
          const g = interpolate(f, [12 + i * 8, 52 + i * 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const h = (alvo / max) * 330 * g;
          const vence = i === 0 ? (values[0] ?? 0) >= (values[1] ?? 0) : (values[1] ?? 0) > (values[0] ?? 0);
          const cor = vence ? accent : "#5b81a8";
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: op }}>
              <div style={{ fontFamily: DISPLAY, fontSize: 64, color: vence ? "#9a5a06" : "#44546a", marginBottom: 16 }}>{Math.round(alvo * g)}{suffix}</div>
              <div style={{ width: 180, height: h, background: `linear-gradient(180deg, ${cor} 0%, ${cor}dd 100%)`, borderRadius: "14px 14px 4px 4px", boxShadow: "0 12px 30px rgba(60,50,30,0.25)" }} />
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 30, color: "#3a3222", marginTop: 20, maxWidth: 260, textAlign: "center" }}>{labels[i] ?? ""}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 06 VERSUS TUG — cabo-de-guerra horizontal: uma barra dividida A|B */
export const Graf06_VersusTug: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = ["A", "B"], values = [50, 50], suffix = "%" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const a = values[0] ?? 50, b = values[1] ?? 50;
  const frac = interpolate(f, [10, 50], [50, (a / (a + b)) * 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#0d0f13", justifyContent: "center", alignItems: "center", padding: "0 160px" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#fff", marginBottom: 56, opacity: op, textAlign: "center" }}>{title}</div>
      <div style={{ width: "100%", maxWidth: 1400, opacity: op }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 34, color: accent }}>{labels[0]} · {Math.round(a)}{suffix}</span>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 34, color: "#8b93a1" }}>{labels[1]} · {Math.round(b)}{suffix}</span>
        </div>
        <div style={{ position: "relative", height: 64, borderRadius: 32, overflow: "hidden", background: "#3d4653" }}>
          <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${frac}%`, background: `linear-gradient(90deg, ${accent} 0%, ${accent}cc 100%)`, boxShadow: `0 0 30px ${accent}66` }} />
          <div style={{ position: "absolute", left: `${frac}%`, top: -6, bottom: -6, width: 6, background: "#fff", boxShadow: "0 0 14px rgba(255,255,255,0.8)" }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 07 TIMELINE RISE — barras por ano subindo, última em destaque */
export const Graf07_TimelineRise: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = [], values = [], suffix = "" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 2 || labels.length !== values.length) return null; // R-32: sem dado real = nada
  const vs = values;
  const ls = labels;
  const max = Math.max(...vs, 1);
  return (
    /* VidRush 24/07: comparativo = card CLARO */
    <AbsoluteFill style={{ background: "#f2eee2", justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px), repeating-linear-gradient(90deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px)" }} />
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#241f16", marginBottom: 54, opacity: op }}>{title}</div>
      <div style={{ display: "flex", gap: 44, alignItems: "flex-end", height: 440, borderBottom: "3px solid rgba(40,34,20,0.35)", padding: "0 30px" }}>
        {vs.map((v, i) => {
          const ult = i === vs.length - 1;
          const g = interpolate(f, [10 + i * 6, 40 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: op }}>
              {ult ? <div style={{ fontFamily: DISPLAY, fontSize: 42, color: "#9a5a06", marginBottom: 12, opacity: g }}>{fmt(v)}{suffix}</div> : null}
              <div style={{ width: 96, height: (v / max) * 360 * g, background: ult ? accent : "#5b81a8", borderRadius: "10px 10px 3px 3px", boxShadow: "0 10px 26px rgba(60,50,30,0.22)" }} />
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: ult ? "#9a5a06" : "#55503f", marginTop: 16 }}>{ls[i]}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 08 LINE PULSE — linha desenhando com ponto pulsante + área */
export const Graf08_LinePulse: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = [], values = [], suffix = "" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 2) return null; // R-32: sem série real = nada
  const vs = values;
  const max = Math.max(...vs, 1), W = 1240, H = 420;
  const pts = vs.map((v, i) => [80 + (i * (W - 160)) / (vs.length - 1), H - 40 - (v / max) * (H - 110)]);
  const prog = interpolate(f, [8, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const nPts = Math.max(2, Math.ceil(pts.length * prog));
  const vis = pts.slice(0, nPts);
  const d = vis.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  const ult = vis[vis.length - 1];
  const pulse = 1 + 0.3 * Math.sin(f / 5);
  return (
    <AbsoluteFill style={{ background: "#0b0d11", justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#fff", marginBottom: 40, opacity: op }}>{title}</div>
      <svg width={W} height={H} style={{ opacity: op }}>
        {[0.25, 0.5, 0.75].map((g, i) => <line key={i} x1={80} x2={W - 80} y1={H - 40 - g * (H - 110)} y2={H - 40 - g * (H - 110)} stroke="rgba(255,255,255,0.08)" strokeWidth={2} />)}
        <line x1={80} x2={W - 80} y1={H - 40} y2={H - 40} stroke="rgba(255,255,255,0.25)" strokeWidth={3} />
        <path d={`${d} L${ult[0]},${H - 40} L80,${H - 40} Z`} fill={`${accent}22`} />
        <path d={d} fill="none" stroke={accent} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 14px ${accent}99)` }} />
        <circle cx={ult[0]} cy={ult[1]} r={13 * pulse} fill={accent} style={{ filter: `drop-shadow(0 0 18px ${accent})` }} />
        {prog >= 0.98 ? <text x={ult[0] - 10} y={ult[1] - 28} fill="#fff" fontFamily={DISPLAY} fontSize={44}>{fmt(vs[vs.length - 1])}{suffix}</text> : null}
      </svg>
    </AbsoluteFill>
  );
};

/* 09 RANK LIST — barras horizontais ranqueadas (top-N) */
export const Graf09_RankList: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = [], values = [], suffix = "" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 2 || labels.length !== values.length) return null; // R-32
  const vs = values;
  const ls = labels;
  const max = Math.max(...vs, 1);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 95% 95% at 50% 40%, #101318 0%, ${BG} 82%)`, justifyContent: "center", padding: "0 220px" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 52, color: "#fff", marginBottom: 50, opacity: op }}>{title}</div>
      {vs.map((v, i) => {
        const g = interpolate(f, [10 + i * 7, 46 + i * 7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
        const lider = i === 0;
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 28, marginBottom: 30, opacity: op }}>
            <div style={{ fontFamily: DISPLAY, fontSize: 44, color: lider ? accent : "#6b7280", width: 70 }}>#{i + 1}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontFamily: SANS, fontWeight: 700, fontSize: 30, color: lider ? "#fff" : "#aab0ba" }}>{ls[i]}</span>
                <span style={{ fontFamily: DISPLAY, fontSize: 32, color: lider ? accent : "#8b93a1" }}>{fmt(v * g)}{suffix}</span>
              </div>
              <div style={{ height: 20, borderRadius: 10, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                <div style={{ width: `${(v / max) * 100 * g}%`, height: "100%", background: lider ? accent : "#46536b", borderRadius: 10, boxShadow: lider ? `0 0 20px ${accent}77` : "none" }} />
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* 10 BIG STAT CARD — cartão: número + label + mini-sparkline */
export const Graf10_BigStatCard: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [], suffix = "" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 24 });
  if (!values.length) return null; // R-32 (QA tenis 23/07: default [..,18] roubou a cena do 25 real)
  const vs = values;
  const alvo = vs[vs.length - 1];
  const v = interpolate(f, [4, 26], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const max = Math.max(...vs, 1);
  const pts = vs.length >= 2 ? vs.map((x, i) => `${i === 0 ? "M" : "L"}${20 + i * (360 / (vs.length - 1))},${120 - (x / max) * 100}`).join(" ") : "";
  return (
    <AbsoluteFill style={{ background: `linear-gradient(155deg, #0f1116 0%, #131019 100%)`, justifyContent: "center", alignItems: "center" }}>
      <div style={{ background: "rgba(255,255,255,0.045)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 26, padding: "70px 110px", textAlign: "center", opacity: s, transform: `translateY(${(1 - s) * 40}px)`, boxShadow: "0 40px 100px rgba(0,0,0,0.6)" }}>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 24, color: accent, letterSpacing: 7, marginBottom: 22 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 160, color: "#fff", lineHeight: 1, textShadow: `0 0 50px ${accent}66` }}>{fmt(v)}{suffix}</div>
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 34, color: "#c3c8d1", marginTop: 20, maxWidth: 760 }}>{title}</div>
        <svg width={400} height={130} style={{ marginTop: 30 }}>
          <path d={pts} fill="none" stroke={accent} strokeWidth={6} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 10px ${accent}88)` }} />
        </svg>
      </div>
    </AbsoluteFill>
  );
};

/* 11 PIE SLICES — pizza real com fatias; 1ª destacada e puxada pra fora */
export const Graf11_PieSlices: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = [], values = [] }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 2 || labels.length !== values.length) return null; // R-32
  const vs = values;
  const ls = labels;
  const total = vs.reduce((a, b) => a + b, 0) || 1;
  const CORES = [accent, "#46536b", "#67748c", "#333c4b", "#8d97a8", "#242b36"];
  const prog = interpolate(f, [8, 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  let acc = 0;
  const R = 250, CX = 300, CY = 290;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 85% at 50% 48%, #11141a 0%, ${BG} 80%)`, justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#fff", marginBottom: 34, opacity: op }}>{title}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 90, opacity: op }}>
        <svg width={600} height={580} viewBox="0 0 600 580">
          {vs.map((v, i) => {
            const a0 = (acc / total) * 2 * Math.PI * prog - Math.PI / 2;
            acc += v;
            const a1 = (acc / total) * 2 * Math.PI * prog - Math.PI / 2;
            const mid = (a0 + a1) / 2;
            const puxa = i === 0 ? 22 : 0;
            const ox = Math.cos(mid) * puxa, oy = Math.sin(mid) * puxa;
            const x0 = CX + ox + R * Math.cos(a0), y0 = CY + oy + R * Math.sin(a0);
            const x1 = CX + ox + R * Math.cos(a1), y1 = CY + oy + R * Math.sin(a1);
            const grande = a1 - a0 > Math.PI ? 1 : 0;
            return <path key={i} d={`M${CX + ox},${CY + oy} L${x0},${y0} A${R},${R} 0 ${grande} 1 ${x1},${y1} Z`} fill={CORES[i % CORES.length]}
              stroke="#0a0b0f" strokeWidth={5} style={i === 0 ? { filter: `drop-shadow(0 0 26px ${accent}66)` } : undefined} />;
          })}
        </svg>
        <div>
          {vs.map((v, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 22 }}>
              <span style={{ width: 26, height: 26, borderRadius: 7, background: CORES[i % CORES.length], flexShrink: 0 }} />
              <span style={{ fontFamily: SANS, fontWeight: i === 0 ? 800 : 600, fontSize: 32, color: i === 0 ? "#fff" : "#aab0ba" }}>
                {ls[i]} · <b style={{ color: i === 0 ? accent : "#c9cdd5" }}>{Math.round((v / total) * 100 * prog)}%</b>
              </span>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 12 MULTI BARS — N barras verticais com labels/valores (não só A vs B) */
export const Graf12_MultiBars: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = [], values = [], suffix = "" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 2 || labels.length !== values.length) return null; // R-32
  const vs = values;
  const ls = labels;
  const max = Math.max(...vs, 1);
  const iMax = vs.indexOf(Math.max(...vs));
  const CORES = [accent, "#5b81a8", "#7a9e5f", "#a86e5b", "#8a6fae", "#5ba89e"];
  return (
    /* VidRush 24/07: comparativo = card CLARO com barras COLORIDAS */
    <AbsoluteFill style={{ background: "#f2eee2", justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px), repeating-linear-gradient(90deg, rgba(90,80,55,0.08) 0 1px, transparent 1px 54px)" }} />
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#241f16", marginBottom: 80, opacity: op }}>{title}</div>
      <div style={{ display: "flex", gap: 58, alignItems: "flex-end", height: 460, borderBottom: "3px solid rgba(40,34,20,0.35)", padding: "0 20px" }}>
        {vs.map((v, i) => {
          const g = interpolate(f, [10 + i * 6, 44 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const top = i === iMax;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: op }}>
              <div style={{ fontFamily: DISPLAY, fontSize: 36, color: top ? "#9a5a06" : "#55503f", marginBottom: 12, opacity: g }}>{fmt(v * g)}{suffix}</div>
              <div style={{ width: 110, height: (v / max) * 340 * g, background: CORES[i % CORES.length], borderRadius: "10px 10px 3px 3px", boxShadow: "0 10px 26px rgba(60,50,30,0.22)" }} />
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: top ? "#241f16" : "#55503f", marginTop: 16, maxWidth: 150, textAlign: "center" }}>{ls[i]}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* 13 DUAL LINE — duas linhas comparadas desenhando (A vs B no tempo) */
export const Graf13_DualLine: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", labels = ["A", "B"], values = [] }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  if (values.length < 4) return null; // R-32: sem 2 séries reais = nada
  const meio = Math.floor(values.length / 2);
  const sA = values.slice(0, meio);
  const sB = values.slice(meio);
  const W = 1240, H = 430, max = Math.max(...sA, ...sB, 1);
  const prog = interpolate(f, [8, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const path = (s: number[]) => {
    const n = Math.max(2, Math.ceil(s.length * prog));
    return s.slice(0, n).map((v, i) => `${i === 0 ? "M" : "L"}${80 + (i * (W - 160)) / (s.length - 1)},${H - 50 - (v / max) * (H - 130)}`).join(" ");
  };
  return (
    <AbsoluteFill style={{ background: "#0b0d11", justifyContent: "center", alignItems: "center" }}>
      <Kicker k={kicker} accent={accent} op={op} />
      <div style={{ fontFamily: DISPLAY, fontSize: 50, color: "#fff", marginBottom: 20, opacity: op }}>{title}</div>
      <div style={{ display: "flex", gap: 60, marginBottom: 20, opacity: op }}>
        <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28, color: accent }}>▬ {labels[0]}</span>
        <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28, color: "#67748c" }}>▬ {labels[1]}</span>
      </div>
      <svg width={W} height={H} style={{ opacity: op }}>
        {[0.33, 0.66].map((g, i) => <line key={i} x1={80} x2={W - 80} y1={H - 50 - g * (H - 130)} y2={H - 50 - g * (H - 130)} stroke="rgba(255,255,255,0.07)" strokeWidth={2} />)}
        <line x1={80} x2={W - 80} y1={H - 50} y2={H - 50} stroke="rgba(255,255,255,0.22)" strokeWidth={3} />
        <path d={path(sB)} fill="none" stroke="#67748c" strokeWidth={6} strokeLinecap="round" />
        <path d={path(sA)} fill="none" stroke={accent} strokeWidth={7} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 12px ${accent}88)` }} />
      </svg>
    </AbsoluteFill>
  );
};

/* ===== OVERLAYS DE GRÁFICO (transparentes — sobre footage; dim aplicado pelo caller) ===== */

/* 14 OVL COUNTER PUNCH — número gigante central com scrim radial (overlay) */
export const Graf14_OvlCounterPunch: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "" }) => {
  const f = useCurrentFrame();
  const alvo = values[0] ?? 0;
  const v = interpolate(f, [6, 50], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 44% 36% at 50% 50%, rgba(0,0,0,0.74) 0%, rgba(0,0,0,0.3) 58%, transparent 80%)" }} />
      {/* position:relative — senão o scrim absoluto pinta POR CIMA do texto estático (CSS painting order) */}
      <div style={{ position: "relative", textAlign: "center", opacity: op }}>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 9, marginBottom: 14 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 170, color: "#fff", lineHeight: 1, textShadow: `0 0 60px ${accent}77, 0 8px 30px rgba(0,0,0,0.9)` }}>{fmt(v)}{suffix}</div>
        <div style={{ fontFamily: DISPLAY, fontSize: 36, color: accent, letterSpacing: 4, marginTop: 18, textTransform: "uppercase", textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>{title}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 15 OVL STAT CORNER — placa compacta de stat no canto inf-dir (overlay) */
export const Graf15_OvlStatCorner: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 22 });
  const v = interpolate(f, [8, 46], [0, values[0] ?? 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", right: 84, bottom: 90, background: "rgba(8,9,12,0.8)", backdropFilter: "blur(5px)", borderTop: `5px solid ${accent}`, borderRadius: 14, padding: "26px 44px", textAlign: "center", opacity: s, transform: `translateY(${(1 - s) * 50}px)`, boxShadow: "0 20px 60px rgba(0,0,0,0.6)" }}>
        {kicker ? <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 20, color: accent, letterSpacing: 5, marginBottom: 8 }}>{kicker.toUpperCase()}</div> : null}
        <div style={{ fontFamily: DISPLAY, fontSize: 84, color: "#fff", lineHeight: 1, textShadow: `0 0 26px ${accent}55` }}>{fmt(v)}{suffix}</div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 24, color: "#c3c8d1", marginTop: 10, maxWidth: 380 }}>{title}</div>
      </div>
    </AbsoluteFill>
  );
};

/* 16 OVL PROGRESS BAR — barra de % fina na base com rótulo (overlay) */
export const Graf16_OvlProgressBar: React.FC<P> = ({ title = "", kicker = "", accent = "#f59e0b", values = [0], suffix = "%" }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const alvo = Math.min(100, values[0] ?? 0);
  const v = interpolate(f, [10, 52], [0, alvo], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end" }}>
      <div style={{ margin: "0 120px 100px", background: "rgba(8,9,12,0.74)", backdropFilter: "blur(5px)", borderRadius: 18, padding: "26px 40px", opacity: op, boxShadow: "0 18px 50px rgba(0,0,0,0.55)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 32, color: "#fff" }}>{kicker ? <b style={{ color: accent, marginRight: 14 }}>{kicker.toUpperCase()}</b> : null}{title}</span>
          <span style={{ fontFamily: DISPLAY, fontSize: 52, color: accent, textShadow: `0 0 20px ${accent}66` }}>{Math.round(v)}{suffix}</span>
        </div>
        <div style={{ height: 18, borderRadius: 9, background: "rgba(255,255,255,0.12)", overflow: "hidden" }}>
          <div style={{ width: `${v}%`, height: "100%", background: `linear-gradient(90deg, ${accent}, ${accent}cc)`, borderRadius: 9, boxShadow: `0 0 18px ${accent}88` }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO ---------------- */
export const GRAFICOS_MANIFEST = [
  { id: 0, comp: "Graf01_CounterGlow", forma: "numero_unico", quando: "número-troféu (18M units, 650K km)" },
  { id: 1, comp: "Graf02_Odometer", forma: "numero_unico", quando: "quilometragem/contagem mecânica (vibe automotiva)" },
  { id: 2, comp: "Graf03_DonutPercent", forma: "percentual", quando: "percentual único limpo (92% uptime)" },
  { id: 3, comp: "Graf04_GaugeMeter", forma: "percentual", quando: "percentual com vibe medidor/velocímetro" },
  { id: 4, comp: "Graf05_VersusBars", forma: "comparacao", quando: "A vs B barras verticais (92% vs 84%)" },
  { id: 5, comp: "Graf06_VersusTug", forma: "comparacao", quando: "A vs B cabo-de-guerra horizontal (share/domínio)" },
  { id: 6, comp: "Graf07_TimelineRise", forma: "tendencia", quando: "crescimento por ano, último destacado" },
  { id: 7, comp: "Graf08_LinePulse", forma: "tendencia", quando: "trajetória/linha com ponto pulsante" },
  { id: 8, comp: "Graf09_RankList", forma: "ranking", quando: "top-N itens com valores (comparativo múltiplo)" },
  { id: 9, comp: "Graf10_BigStatCard", forma: "numero_unico", quando: "stat premium em cartão com sparkline" },
  { id: 10, comp: "Graf11_PieSlices", forma: "distribuicao", quando: "pizza com fatias (share/composição), 1ª destacada" },
  { id: 11, comp: "Graf12_MultiBars", forma: "serie", quando: "N barras verticais (vários itens/anos)" },
  { id: 12, comp: "Graf13_DualLine", forma: "tendencia", quando: "duas linhas comparadas no tempo (A vs B)" },
  { id: 13, comp: "Graf14_OvlCounterPunch", forma: "numero_unico", overlay: true, quando: "número gigante SOBRE footage (scrim + dim)" },
  { id: 14, comp: "Graf15_OvlStatCorner", forma: "numero_unico", overlay: true, quando: "placa de stat no canto SOBRE footage" },
  { id: 15, comp: "Graf16_OvlProgressBar", forma: "percentual", overlay: true, quando: "barra de % na base SOBRE footage" },
];

export const GRAFICOS_COMPS: Record<string, React.FC<P>> = {
  Graf01_CounterGlow, Graf02_Odometer, Graf03_DonutPercent, Graf04_GaugeMeter, Graf05_VersusBars,
  Graf06_VersusTug, Graf07_TimelineRise, Graf08_LinePulse, Graf09_RankList, Graf10_BigStatCard,
  Graf11_PieSlices, Graf12_MultiBars, Graf13_DualLine, Graf14_OvlCounterPunch, Graf15_OvlStatCorner,
  Graf16_OvlProgressBar,
};
