import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { geoMercator, geoPath, geoCentroid } from "d3-geo";
import { feature } from "topojson-client";
// @ts-ignore — quirk conhecido do JSON (bundler resolve)
import world from "world-atlas/countries-110m.json";

/* ============================================================
   ALMOXARIFADO DE MAPAS — 8 variações (2026-07-20).
   NÚCLEO = VALIDAÇÃO GEO + AUTO-ENQUADRAMENTO: o mapa SEMPRE ilustra
   o que o roteiro cita — país resolvido por alias (continente = REJEITADO),
   fitExtent nos países/pontos falados. Sem dado válido -> builder recusa.
   CONTRATO: { paises?: string[], pontos?: {nome,lat,lon}[], valores?: string[],
              titulo?, kicker?, accent? }
   ============================================================ */

type Ponto = { nome?: string; lat: number; lon: number };
type P = {
  paises?: string[]; pontos?: Ponto[]; valores?: string[]; titulo?: string; kicker?: string; accent?: string;
  /* variações satélite/ruas (Map09-12): imagens ESRI pré-baixadas pelo executor */
  sat?: string[]; halfs?: number[]; bbox?: number[]; // bbox mercator [xmin,ymin,xmax,ymax] da imagem de ruas
  images?: string[]; // Map13: foto do lugar (slot preenchido pelo executor via gate)
};

const DISPLAY = F_DISPLAY;
const MONO = F_MONO;
const SANS = F_SANS;
const MAR = "#0d1420";
const TERRA = "#1b2434";
const TRACO = "#2c3850";

/* ---------------- GEO CORE (validação + fit) ---------------- */
const FEATURES: any[] = (feature(world as any, (world as any).objects.countries) as any).features;

const ALIAS: Record<string, string> = {
  "united states": "united states of america", "usa": "united states of america", "us": "united states of america",
  "uk": "united kingdom", "britain": "united kingdom", "great britain": "united kingdom",
  "uae": "united arab emirates", "emirates": "united arab emirates",
  "drc": "dem. rep. congo", "democratic republic of congo": "dem. rep. congo",
  "ivory coast": "côte d'ivoire", "czech republic": "czechia", "burma": "myanmar",
  "south korea": "south korea", "north korea": "north korea", "russia": "russia",
};
const CONTINENTES = new Set(["north america", "south america", "europe", "asia", "africa", "oceania",
  "antarctica", "middle east", "latin america", "central america", "worldwide", "global", "the world"]);

export function resolverPais(nome: string): any | null {
  const n = (nome || "").trim().toLowerCase();
  if (!n || CONTINENTES.has(n)) return null;           // continente/vazio = REJEITA
  const alvo = ALIAS[n] || n;
  let hit = FEATURES.find((f) => (f.properties?.name || "").toLowerCase() === alvo);
  if (!hit) hit = FEATURES.find((f) => (f.properties?.name || "").toLowerCase().includes(alvo) || alvo.includes((f.properties?.name || "").toLowerCase()));
  return hit || null;
}

/* validação exportada p/ o registry/Diretor decidir ANTES de escolher a variação */
export function validarGeo(d: { paises?: string[]; pontos?: Ponto[] }) {
  const paisesOk = (d.paises || []).map((p) => resolverPais(p)).filter(Boolean);
  const pontosOk = (d.pontos || []).filter((pt) => pt && typeof pt.lat === "number" && typeof pt.lon === "number" &&
    Math.abs(pt.lat) <= 85 && Math.abs(pt.lon) <= 180);
  return { paisesOk, pontosOk, temPais: paisesOk.length > 0, temPonto: pontosOk.length > 0 };
}

/* projeção enquadrada no que foi citado (países + pontos), com folga */
function projecaoFit(feats: any[], pontos: Ponto[], w: number, h: number, folga = 0.22) {
  const proj = geoMercator();
  const geos: any[] = [...feats];
  if (!feats.length && pontos.length === 1) {
    // ponto único: fitExtent em área zero degenera (escala infinita) — cantos ±8°/±6° como
    // MultiPoint (polígono esférico tem winding e pode virar o COMPLEMENTO do box no d3-geo)
    const { lon, lat } = pontos[0];
    const la = Math.max(-78, Math.min(78, lat));
    geos.push({ type: "MultiPoint", coordinates: [[lon - 8, la - 6], [lon + 8, la + 6]] });
  } else if (pontos.length) {
    geos.push({ type: "MultiPoint", coordinates: pontos.map((p) => [p.lon, p.lat]) });
  }
  const alvo = geos.length === 1 ? geos[0] : { type: "GeometryCollection", geometries: geos.map((g) => g.geometry || g) };
  try {
    proj.fitExtent([[w * folga, h * folga], [w * (1 - folga), h * (1 - folga)]], alvo as any);
  } catch {
    proj.scale(300).center([0, 20]).translate([w / 2, h / 2]);
  }
  if (!isFinite(proj.scale()) || !isFinite(proj.translate()[0]) || !isFinite(proj.translate()[1])) {
    proj.scale(300).center([0, 20]).translate([w / 2, h / 2]);
  }
  // teto de zoom (país minúsculo não vira "mancha gigante")
  if (proj.scale() > 3200) proj.scale(3200);
  return proj;
}

/* mundo de fundo + países destacados */
const Mundo: React.FC<{ proj: any; destacados?: any[]; accent: string; glow?: number }> = ({ proj, destacados = [], accent, glow = 1 }) => {
  const path = geoPath(proj);
  const nomes = new Set(destacados.map((d) => d.properties?.name));
  return (
    <g>
      {FEATURES.map((f, i) => (
        <path key={i} d={path(f) || undefined} fill={nomes.has(f.properties?.name) ? "none" : TERRA} stroke={TRACO} strokeWidth={0.6} />
      ))}
      {destacados.map((f, i) => (
        <path key={"d" + i} d={path(f) || undefined} fill={accent} stroke="#ffd9a0" strokeWidth={1.4}
          style={{ filter: `drop-shadow(0 0 ${14 * glow}px ${accent}aa)` }} opacity={0.92} />
      ))}
    </g>
  );
};

const Base: React.FC<{ children: React.ReactNode; kicker?: string; accent?: string }> = ({ children, kicker, accent = "#f59e0b" }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 95% 95% at 50% 45%, ${MAR} 0%, #070b12 85%)` }}>
    <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(140,160,220,0.05) 0 1px, transparent 1px 90px), repeating-linear-gradient(90deg, rgba(140,160,220,0.05) 0 1px, transparent 1px 90px)" }} />
    {children}
    {kicker ? <div style={{ position: "absolute", top: 62, left: 0, right: 0, textAlign: "center", fontFamily: SANS, fontWeight: 700, fontSize: 25, color: accent, letterSpacing: 8 }}>{kicker.toUpperCase()}</div> : null}
    <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0 2px, transparent 2px 4px)", pointerEvents: "none" }} />
  </AbsoluteFill>
);

/* 01 COUNTRY FOCUS — um país acende + fit nele + label central */
export const Map01_CountryFocus: React.FC<P> = ({ paises = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ paises });
  if (!g.temPais) return null;
  const alvo = g.paisesOk[0];
  const proj = projecaoFit([alvo], [], 1920, 1080, 0.26);
  const op = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const pulse = 0.75 + 0.25 * Math.sin(f / 9);
  const [cx, cy] = proj(geoCentroid(alvo)) || [960, 540];
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} destacados={[alvo]} accent={accent} glow={pulse} />
        <circle cx={cx} cy={cy} r={10 + 6 * pulse} fill="none" stroke="#fff" strokeWidth={2.5} opacity={0.85} />
        <circle cx={cx} cy={cy} r={5} fill="#fff" />
      </svg>
      <div style={{ position: "absolute", bottom: 92, left: 0, right: 0, textAlign: "center", opacity: op }}>
        <span style={{ fontFamily: DISPLAY, fontSize: 62, color: "#fff", background: "rgba(0,0,0,0.55)", padding: "12px 44px", borderRadius: 14, textShadow: `0 0 30px ${accent}66` }}>
          {titulo || alvo.properties?.name}
        </span>
      </div>
    </Base>
  );
};

/* 02 MULTI HIGHLIGHT — N países acendem em sequência + cards SÓ com o que for válido */
export const Map02_MultiHighlight: React.FC<P> = ({ paises = [], valores = [], kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ paises });
  if (g.paisesOk.length < 2) return null;
  const proj = projecaoFit(g.paisesOk, [], 1920, 1080, 0.2);
  const path = geoPath(proj);
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} accent={accent} />
        {g.paisesOk.map((ft, i) => {
          const e = interpolate(f, [12 + i * 10, 26 + i * 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return <path key={i} d={path(ft) || undefined} fill={accent} opacity={0.92 * e} stroke="#ffd9a0" strokeWidth={1.3} style={{ filter: `drop-shadow(0 0 12px ${accent}88)` }} />;
        })}
      </svg>
      <div style={{ position: "absolute", right: 90, top: "50%", transform: "translateY(-50%)", display: "flex", flexDirection: "column", gap: 18 }}>
        {g.paisesOk.slice(0, 5).map((ft, i) => {
          const e = interpolate(f, [16 + i * 10, 30 + i * 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const val = (valores[i] || "").trim();
          return (
            <div key={i} style={{ background: "rgba(8,10,15,0.82)", borderLeft: `5px solid ${accent}`, borderRadius: 10, padding: "14px 26px", opacity: e, transform: `translateX(${(1 - e) * 50}px)`, minWidth: 260 }}>
              <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28, color: "#fff" }}>{ft.properties?.name}</div>
              {val ? <div style={{ fontFamily: DISPLAY, fontSize: 34, color: accent, marginTop: 4 }}>{val}</div> : null}
            </div>
          );
        })}
      </div>
    </Base>
  );
};

/* 03 ROUTE ARC — rota A→B com arco animado (EXIGE 2 pontos com lat/lon) */
export const Map03_RouteArc: React.FC<P> = ({ pontos = [], kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ pontos });
  if (g.pontosOk.length < 2) return null;
  const [A, B] = g.pontosOk;
  const proj = projecaoFit([], [A, B], 1920, 1080, 0.24);
  const [ax, ay] = proj([A.lon, A.lat]) || [0, 0];
  const [bx, by] = proj([B.lon, B.lat]) || [0, 0];
  const mx = (ax + bx) / 2, my = Math.min(ay, by) - Math.hypot(bx - ax, by - ay) * 0.28;
  const draw = interpolate(f, [14, 64], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const Pin: React.FC<{ x: number; y: number; nome?: string; vis: number }> = ({ x, y, nome, vis }) => (
    <g opacity={vis}>
      <circle cx={x} cy={y} r={13} fill={accent} style={{ filter: `drop-shadow(0 0 12px ${accent})` }} />
      <circle cx={x} cy={y} r={5.5} fill="#fff" />
      {nome ? <foreignObject x={x - 160} y={y + 20} width={320} height={70}>
        <div style={{ textAlign: "center" }}><span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 30, color: "#fff", background: "rgba(0,0,0,0.72)", padding: "6px 20px", borderRadius: 10 }}>{nome}</span></div>
      </foreignObject> : null}
    </g>
  );
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} accent={accent} />
        <path d={`M ${ax} ${ay} Q ${mx} ${my} ${bx} ${by}`} fill="none" stroke={accent} strokeWidth={6}
          strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw}
          style={{ filter: `drop-shadow(0 0 12px ${accent}aa)` }} />
        <Pin x={ax} y={ay} nome={A.nome} vis={1} />
        <Pin x={bx} y={by} nome={B.nome} vis={draw > 0.92 ? 1 : 0} />
      </svg>
    </Base>
  );
};

/* 04 PIN CALLOUT — 1 ponto com pin pulsante + card de local */
export const Map04_PinCallout: React.FC<P> = ({ pontos = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ pontos });
  if (!g.temPonto) return null;
  const pt = g.pontosOk[0];
  const proj = projecaoFit([], [pt], 1920, 1080, 0.34);
  const [x, y] = proj([pt.lon, pt.lat]) || [960, 540];
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const ring = (f % 46) / 46;
  const { fps } = useVideoConfig();
  const s = spring({ frame: f - 14, fps, config: { damping: 13, stiffness: 130 }, durationInFrames: 20 });
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} accent={accent} />
        <circle cx={x} cy={y} r={16 + ring * 46} fill="none" stroke={accent} strokeWidth={3} opacity={1 - ring} />
        <circle cx={x} cy={y} r={14} fill={accent} style={{ filter: `drop-shadow(0 0 16px ${accent})` }} />
        <circle cx={x} cy={y} r={6} fill="#fff" />
      </svg>
      <div style={{ position: "absolute", left: x + 44, top: y - 66, background: "rgba(8,10,15,0.86)", border: `1px solid ${accent}66`, borderLeft: `6px solid ${accent}`, borderRadius: 12, padding: "18px 30px", opacity: s, transform: `translateX(${(1 - s) * 30}px)` }}>
        <div style={{ fontFamily: DISPLAY, fontSize: 40, color: "#fff" }}>{pt.nome || titulo}</div>
        {titulo && pt.nome ? <div style={{ fontFamily: SANS, fontSize: 24, color: accent, marginTop: 4 }}>{titulo}</div> : null}
        <div style={{ fontFamily: MONO, fontSize: 19, color: "#7d94b8", marginTop: 8 }}>{Math.abs(pt.lat).toFixed(2)}°{pt.lat >= 0 ? "N" : "S"} · {Math.abs(pt.lon).toFixed(2)}°{pt.lon >= 0 ? "E" : "W"}</div>
      </div>
    </Base>
  );
};

/* 05 REGION ZOOM — mergulho: mundo inteiro → zoom no país destacado */
export const Map05_RegionZoom: React.FC<P> = ({ paises = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ paises });
  if (!g.temPais) return null;
  const alvo = g.paisesOk[0];
  const projFim = projecaoFit([alvo], [], 1920, 1080, 0.3);
  const projIni = geoMercator().scale(240).center([10, 25]).translate([960, 540]);
  const t = interpolate(f, [8, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const proj = geoMercator()
    .scale(projIni.scale() + (projFim.scale() - projIni.scale()) * t)
    .translate([
      projIni.translate()[0] + (projFim.translate()[0] - projIni.translate()[0]) * t,
      projIni.translate()[1] + (projFim.translate()[1] - projIni.translate()[1]) * t,
    ]);
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const lblOp = interpolate(f, [66, 82], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} destacados={[alvo]} accent={accent} />
      </svg>
      <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, textAlign: "center", opacity: lblOp }}>
        <span style={{ fontFamily: DISPLAY, fontSize: 58, color: "#fff", background: "rgba(0,0,0,0.6)", padding: "12px 42px", borderRadius: 14 }}>{titulo || alvo.properties?.name}</span>
      </div>
    </Base>
  );
};

/* 06 PATH TRAIL — trilha desenhando por N pontos (expedição multi-parada) */
export const Map06_PathTrail: React.FC<P> = ({ pontos = [], kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ pontos });
  if (g.pontosOk.length < 3) return null;
  const proj = projecaoFit([], g.pontosOk, 1920, 1080, 0.22);
  const xy = g.pontosOk.map((p) => proj([p.lon, p.lat]) || [0, 0]);
  const d = xy.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ");
  const draw = interpolate(f, [12, 92], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} accent={accent} />
        <path d={d} fill="none" stroke={accent} strokeWidth={5} strokeDasharray="14 12" pathLength={1}
          strokeDashoffset={1 - draw} style={{ filter: `drop-shadow(0 0 10px ${accent}99)` }} />
        {xy.map(([x, y], i) => {
          const vis = draw >= i / (xy.length - 1) - 0.02 ? 1 : 0;
          return (
            <g key={i} opacity={vis}>
              <circle cx={x} cy={y} r={11} fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} />
              <circle cx={x} cy={y} r={4.5} fill="#fff" />
              {g.pontosOk[i].nome ? <foreignObject x={x - 150} y={y - 66} width={300} height={52}>
                <div style={{ textAlign: "center" }}><span style={{ fontFamily: SANS, fontWeight: 700, fontSize: 24, color: "#fff", background: "rgba(0,0,0,0.7)", padding: "4px 16px", borderRadius: 8 }}>{g.pontosOk[i].nome}</span></div>
              </foreignObject> : null}
            </g>
          );
        })}
      </svg>
    </Base>
  );
};

/* 07 RADAR SWEEP — zona de operação com varredura de radar num ponto */
export const Map07_RadarSweep: React.FC<P> = ({ pontos = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const g = validarGeo({ pontos });
  if (!g.temPonto) return null;
  const pt = g.pontosOk[0];
  const proj = projecaoFit([], [pt], 1920, 1080, 0.36);
  const [x, y] = proj([pt.lon, pt.lat]) || [960, 540];
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const ang = (f * 3.2) % 360;
  const R = 240;
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} accent={accent} />
        {[0.35, 0.65, 1].map((k, i) => <circle key={i} cx={x} cy={y} r={R * k} fill="none" stroke={`${accent}55`} strokeWidth={1.6} />)}
        <line x1={x - R} x2={x + R} y1={y} y2={y} stroke={`${accent}33`} strokeWidth={1.2} />
        <line x1={x} x2={x} y1={y - R} y2={y + R} stroke={`${accent}33`} strokeWidth={1.2} />
        <path d={`M ${x} ${y} L ${x + R * Math.cos((ang - 26) * Math.PI / 180)} ${y + R * Math.sin((ang - 26) * Math.PI / 180)} A ${R} ${R} 0 0 1 ${x + R * Math.cos(ang * Math.PI / 180)} ${y + R * Math.sin(ang * Math.PI / 180)} Z`}
          fill={`${accent}2e`} />
        <line x1={x} y1={y} x2={x + R * Math.cos(ang * Math.PI / 180)} y2={y + R * Math.sin(ang * Math.PI / 180)} stroke={accent} strokeWidth={3} style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
        <circle cx={x} cy={y} r={7} fill="#fff" />
      </svg>
      {(pt.nome || titulo) ? <div style={{ position: "absolute", left: x + R * 0.75, top: y - R - 20, fontFamily: MONO, fontSize: 27, color: accent, background: "rgba(0,0,0,0.72)", padding: "8px 22px", borderRadius: 8, letterSpacing: 3 }}>{(pt.nome || titulo).toUpperCase()}</div> : null}
    </Base>
  );
};

/* 08 STAT MAP — país destacado + stat gigante lateral (dado ancorado) */
export const Map08_StatMap: React.FC<P> = ({ paises = [], valores = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = validarGeo({ paises });
  const stat = (valores[0] || "").trim();
  if (!g.temPais || !stat) return null;
  const alvo = g.paisesOk[0];
  const proj = projecaoFit([alvo], [], 1920, 1080, 0.3);
  // desloca o mapa pra esquerda (stat ocupa a direita)
  proj.translate([proj.translate()[0] - 320, proj.translate()[1]]);
  const op = interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const s = spring({ frame: f - 16, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 24 });
  return (
    <Base kicker={kicker} accent={accent}>
      <svg width={1920} height={1080} style={{ opacity: op }}>
        <Mundo proj={proj} destacados={[alvo]} accent={accent} />
      </svg>
      <div style={{ position: "absolute", right: 110, top: "50%", transform: `translateY(-50%) translateX(${(1 - s) * 70}px)`, opacity: s, textAlign: "right", maxWidth: 620 }}>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 32, color: "#c9d2e0", marginBottom: 10 }}>{alvo.properties?.name}</div>
        <div style={{ fontFamily: DISPLAY, fontSize: 150, color: "#fff", lineHeight: 1, textShadow: `0 0 50px ${accent}66` }}>{stat}</div>
        {titulo ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 30, color: accent, marginTop: 14 }}>{titulo}</div> : null}
        <div style={{ width: 130, height: 6, background: accent, borderRadius: 3, marginTop: 22, marginLeft: "auto", boxShadow: `0 0 18px ${accent}` }} />
      </div>
    </Base>
  );
};

/* ============ SATÉLITE / RUAS (estilo Google Earth / Google Maps) ============
   Imagens ESRI (World_Imagery / World_Street_Map) baixadas ANTES pelo executor
   (satelite_fetch.py) — componente NUNCA busca rede; sem imagem => recusa. */

const srcSat = (p: string) => (/^(https?:|[A-Za-z]:)/.test(p) ? p : staticFile(p));
const suave = (x: number, a: number, b: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const MERC_R = 6378137;
const merc = (lon: number, lat: number): [number, number] =>
  [(lon * Math.PI / 180) * MERC_R, Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * MERC_R];

/* 09 EARTH ZOOM — mergulho Google-Earth: do espaço até o local (pilha de níveis) */
export const Map09_EarthZoom: React.FC<P> = ({ sat = [], halfs = [], pontos = [], titulo = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps, durationInFrames: F } = useVideoConfig();
  const g = validarGeo({ pontos });
  if (sat.length < 3 || sat.length !== halfs.length || !g.temPonto) return null;
  const pt = g.pontosOk[0];
  const us = halfs.map((h) => Math.log(h));
  const zoomEnd = 0.8;
  const tz = suave(f / F, 0, zoomEnd);
  const logZ = interpolate(tz, [0, 1], [us[0], us[us.length - 1]]);
  const settle = suave(f / F, zoomEnd - 0.1, zoomEnd + 0.02);
  const showLon = interpolate(settle, [0, 1], [pt.lon - 6, pt.lon]);
  const showLat = interpolate(settle, [0, 1], [pt.lat + 6, pt.lat]);
  const lockIn = spring({ frame: f - Math.round(F * zoomEnd), fps, config: { damping: 14 }, durationInFrames: 22 });
  const labelIn = spring({ frame: f - Math.round(F * (zoomEnd + 0.04)), fps, config: { damping: 13 }, durationInFrames: 18 });
  return (
    <AbsoluteFill style={{ background: "#04070d", overflow: "hidden" }}>
      {sat.map((s, i) => {
        const scale = Math.exp(us[i] - logZ);
        const appear = i === 0 ? 1 : suave(scale, 1.0, 1.4);
        const nextAppear = i < sat.length - 1 ? suave(Math.exp(us[i + 1] - logZ), 1.0, 1.4) : 0;
        const op = Math.max(0, Math.min(1, appear) * (1 - nextAppear));
        if (op < 0.003 || scale < 0.2) return null;
        return (
          <AbsoluteFill key={i} style={{ opacity: op }}>
            <Img src={srcSat(s)} style={{ width: 1920, height: 1080, objectFit: "cover", transform: `scale(${scale.toFixed(4)})`, transformOrigin: "center center" }} />
          </AbsoluteFill>
        );
      })}
      <AbsoluteFill style={{ pointerEvents: "none", boxShadow: "inset 0 0 320px 90px rgba(0,0,0,0.72)" }} />
      <div style={{ position: "absolute", top: 42, left: 50, fontFamily: MONO, color: accent, fontSize: 23, letterSpacing: 1, textShadow: "0 1px 6px rgba(0,0,0,0.9)", lineHeight: 1.7 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 9, height: 9, borderRadius: "50%", background: accent, opacity: 0.4 + 0.6 * Math.abs(Math.sin(f / 7)) }} />
          SATELLITE
        </div>
        <div>LAT {Math.abs(showLat).toFixed(4)}° {showLat >= 0 ? "N" : "S"}</div>
        <div>LON {Math.abs(showLon).toFixed(4)}° {showLon >= 0 ? "E" : "W"}</div>
      </div>
      {lockIn > 0.01 && (
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
          <g opacity={lockIn} transform="translate(960 540)">
            <circle r={54 + 30 * (1 - lockIn)} fill="none" stroke={accent} strokeWidth={2.5} opacity={0.9} />
            <circle r={6} fill={accent} />
            {[0, 90, 180, 270].map((a) => <line key={a} transform={`rotate(${a})`} y1={-40} y2={-72} stroke={accent} strokeWidth={2.5} />)}
          </g>
        </svg>
      )}
      {labelIn > 0.01 && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 104, textAlign: "center", opacity: labelIn, transform: `translateY(${(1 - labelIn) * 20}px)` }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 46, color: "#fff", background: "rgba(4,10,18,0.68)", border: `1px solid ${accent}`, padding: "12px 36px", borderRadius: 10 }}>
            {pt.nome || titulo}
          </span>
        </div>
      )}
    </AbsoluteFill>
  );
};

/* 10 SAT PIN APP — satélite parado + pin gota estilo app de mapas + card branco */
export const Map10_SatPinApp: React.FC<P> = ({ sat = [], pontos = [], titulo = "", accent = "#ea4335" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = validarGeo({ pontos });
  if (!sat[0] || !g.temPonto) return null;
  const pt = g.pontosOk[0];
  const zoom = interpolate(f, [0, 160], [1.06, 1.2], { extrapolateRight: "clamp" });
  const drop = spring({ frame: f - 14, fps, config: { damping: 11, stiffness: 160 }, durationInFrames: 22 });
  const card = spring({ frame: f - 30, fps, config: { damping: 13 }, durationInFrames: 20 });
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#0a0d12", overflow: "hidden", opacity: op }}>
      <Img src={srcSat(sat[0])} style={{ width: 1920, height: 1080, objectFit: "cover", transform: `scale(${zoom})`, transformOrigin: "50% 45%" }} />
      <AbsoluteFill style={{ pointerEvents: "none", boxShadow: "inset 0 0 260px 60px rgba(0,0,0,0.55)" }} />
      {/* pin gota caindo no centro */}
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <ellipse cx={960} cy={556} rx={26 * drop} ry={9 * drop} fill="rgba(0,0,0,0.45)" />
        <g transform={`translate(960 ${556 - 92 * drop + 92}) scale(${Math.max(0.01, drop) * 1.55})`} opacity={Math.min(1, drop * 2)}>
          <path d="M0-46c-12.7 0-23 10.3-23 23 0 17.3 23 46 23 46s23-28.7 23-46c0-12.7-10.3-23-23-23z" fill={accent} stroke="#fff" strokeWidth={2.5} />
          <circle cy={-23} r={8} fill="#fff" />
        </g>
      </svg>
      {/* card branco estilo app */}
      <div style={{ position: "absolute", left: 1040, top: 400, background: "#fff", borderRadius: 16, padding: "22px 32px", boxShadow: "0 14px 44px rgba(0,0,0,0.5)", opacity: card, transform: `translateY(${(1 - card) * 26}px)`, minWidth: 340 }}>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, color: "#1a1c20" }}>{pt.nome || titulo}</div>
        {titulo && pt.nome ? <div style={{ fontFamily: SANS, fontSize: 24, color: "#5f6672", marginTop: 4 }}>{titulo}</div> : null}
        <div style={{ fontFamily: MONO, fontSize: 18, color: "#9aa2ae", marginTop: 10 }}>
          {Math.abs(pt.lat).toFixed(4)}°{pt.lat >= 0 ? "N" : "S"} {Math.abs(pt.lon).toFixed(4)}°{pt.lon >= 0 ? "E" : "W"}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 11 STREET ROUTE — rota A→B animada sobre mapa de RUAS (estilo app de navegação);
   km REAL calculado das coordenadas (haversine) — nada inventado */
export const Map11_StreetRoute: React.FC<P> = ({ sat = [], bbox = [], pontos = [], kicker = "", accent = "#2f6fed" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = validarGeo({ pontos });
  if (!sat[0] || bbox.length !== 4 || g.pontosOk.length < 2) return null;
  const [A, B] = g.pontosOk;
  const [xmin, ymin, xmax, ymax] = bbox;
  const px = (p: Ponto): [number, number] => {
    const [mx, my] = merc(p.lon, p.lat);
    return [((mx - xmin) / (xmax - xmin)) * 1920, ((ymax - my) / (ymax - ymin)) * 1080];
  };
  const [ax, ay] = px(A), [bx, by] = px(B);
  const dLat = ((B.lat - A.lat) * Math.PI) / 180, dLon = ((B.lon - A.lon) * Math.PI) / 180;
  const km = Math.round(2 * 6371 * Math.asin(Math.sqrt(
    Math.sin(dLat / 2) ** 2 + Math.cos((A.lat * Math.PI) / 180) * Math.cos((B.lat * Math.PI) / 180) * Math.sin(dLon / 2) ** 2)));
  const mx2 = (ax + bx) / 2 + (by - ay) * 0.12, my2 = (ay + by) / 2 + (ax - bx) * 0.12;
  const draw = interpolate(f, [16, 74], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const chip = spring({ frame: f - 76, fps, config: { damping: 13 }, durationInFrames: 18 });
  const op = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#e8eaed", overflow: "hidden", opacity: op }}>
      <Img src={srcSat(sat[0])} style={{ width: 1920, height: 1080, objectFit: "cover" }} />
      <AbsoluteFill style={{ pointerEvents: "none", boxShadow: "inset 0 0 220px 40px rgba(0,0,0,0.28)" }} />
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <path d={`M ${ax} ${ay} Q ${mx2} ${my2} ${bx} ${by}`} fill="none" stroke="#fff" strokeWidth={13} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} opacity={0.9} />
        <path d={`M ${ax} ${ay} Q ${mx2} ${my2} ${bx} ${by}`} fill="none" stroke={accent} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />
        <circle cx={ax} cy={ay} r={13} fill="#fff" stroke={accent} strokeWidth={5} />
        {draw > 0.96 ? (
          <g transform={`translate(${bx} ${by}) scale(1.35)`}>
            <path d="M0-46c-12.7 0-23 10.3-23 23 0 17.3 23 46 23 46s23-28.7 23-46c0-12.7-10.3-23-23-23z" fill="#ea4335" stroke="#fff" strokeWidth={2.5} />
            <circle cy={-23} r={8} fill="#fff" />
          </g>
        ) : null}
      </svg>
      {/* labels dos extremos */}
      {[{ p: A, x: ax, y: ay }, { p: B, x: bx, y: by }].map(({ p, x, y }, i) => (
        p.nome ? <div key={i} style={{ position: "absolute", left: x - 150, top: y + (i === 0 ? 24 : 34), width: 300, textAlign: "center", opacity: i === 0 ? 1 : (draw > 0.96 ? 1 : 0) }}>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 27, color: "#1a1c20", background: "rgba(255,255,255,0.92)", padding: "5px 18px", borderRadius: 9, boxShadow: "0 3px 12px rgba(0,0,0,0.3)" }}>{p.nome}</span>
        </div> : null
      ))}
      {/* chip de distância REAL (haversine das coords) */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 74, textAlign: "center", opacity: chip, transform: `translateY(${(1 - chip) * -18}px)` }}>
        <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 32, color: "#fff", background: accent, padding: "10px 30px", borderRadius: 999, boxShadow: "0 6px 22px rgba(0,0,0,0.35)" }}>
          {kicker ? kicker + " · " : ""}≈ {km} km
        </span>
      </div>
    </AbsoluteFill>
  );
};

/* 12 SAT TARGET — satélite com push-in lento + brackets de alvo + HUD (vibe recon) */
export const Map12_SatTarget: React.FC<P> = ({ sat = [], pontos = [], titulo = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = validarGeo({ pontos });
  if (!sat[0] || !g.temPonto) return null;
  const pt = g.pontosOk[0];
  const zoom = interpolate(f, [0, 160], [1.04, 1.38], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  const lock = spring({ frame: f - 26, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 26 });
  const bs = 320 - 210 * lock; // brackets fecham no alvo
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#04070d", overflow: "hidden", opacity: op }}>
      <Img src={srcSat(sat[0])} style={{ width: 1920, height: 1080, objectFit: "cover", transform: `scale(${zoom})`, transformOrigin: "center center", filter: "saturate(0.85) contrast(1.06)" }} />
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(140,180,230,0.07) 0 1px, transparent 1px 120px), repeating-linear-gradient(90deg, rgba(140,180,230,0.07) 0 1px, transparent 1px 120px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ pointerEvents: "none", boxShadow: "inset 0 0 300px 80px rgba(0,0,0,0.7)" }} />
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <g stroke={accent} strokeWidth={4} fill="none" opacity={0.95} style={{ filter: `drop-shadow(0 0 8px ${accent}aa)` }}>
          {[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy], i) => (
            <path key={i} d={`M ${960 + sx * bs} ${540 + sy * bs - sy * 46} L ${960 + sx * bs} ${540 + sy * bs} L ${960 + sx * bs - sx * 46} ${540 + sy * bs}`} />
          ))}
        </g>
        <line x1={935} x2={985} y1={540} y2={540} stroke={accent} strokeWidth={2} opacity={lock} />
        <line x1={960} x2={960} y1={515} y2={565} stroke={accent} strokeWidth={2} opacity={lock} />
      </svg>
      <div style={{ position: "absolute", top: 42, right: 56, textAlign: "right", fontFamily: MONO, color: accent, fontSize: 22, letterSpacing: 2, textShadow: "0 1px 6px rgba(0,0,0,0.9)", lineHeight: 1.8 }}>
        <div>{Math.abs(pt.lat).toFixed(4)}° {pt.lat >= 0 ? "N" : "S"} · {Math.abs(pt.lon).toFixed(4)}° {pt.lon >= 0 ? "E" : "W"}</div>
        <div style={{ opacity: lock }}>TARGET LOCKED</div>
      </div>
      {(pt.nome || titulo) ? (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 96, textAlign: "center", opacity: lock }}>
          <span style={{ fontFamily: DISPLAY, fontSize: 44, color: "#fff", background: "rgba(4,10,18,0.66)", border: `1px solid ${accent}`, padding: "10px 34px", borderRadius: 10 }}>
            {(pt.nome || titulo).toUpperCase()}
          </span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/* 13 CINE LOCATION — cartão cinematográfico de local: foto full-bleed + LETTERBOX
   (faixas pretas) + painel lateral com MAPA do lugar + texto. Foto via slot do
   executor (gate); mapa geo-validado — sem foto OU sem geo => recusa. */
export const Map13_CineLocation: React.FC<P> = ({ images = [], paises = [], pontos = [], titulo = "", kicker = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = validarGeo({ paises, pontos });
  if (!images[0] || (!g.temPais && !g.temPonto)) return null;
  const alvo = g.paisesOk[0] || null;
  const MW = 560, MH = 430;
  const proj = alvo ? projecaoFit([alvo], g.pontosOk, MW, MH, 0.16) : projecaoFit([], g.pontosOk, MW, MH, 0.3);
  const path = geoPath(proj);
  const pin = g.temPonto ? proj([g.pontosOk[0].lon, g.pontosOk[0].lat]) : (alvo ? proj(geoCentroid(alvo)) : null);
  const nome = g.pontosOk[0]?.nome || titulo || alvo?.properties?.name || "";

  const bar = interpolate(f, [0, 16], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const zoom = interpolate(f, [0, 160], [1.1, 1.0], { extrapolateRight: "clamp" });
  const painel = spring({ frame: f - 12, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 26 });
  const txt1 = spring({ frame: f - 24, fps, config: { damping: 13 }, durationInFrames: 20 });
  const txt2 = spring({ frame: f - 34, fps, config: { damping: 13 }, durationInFrames: 20 });
  const mapa = spring({ frame: f - 42, fps, config: { damping: 14 }, durationInFrames: 24 });
  const pulse = 0.7 + 0.3 * Math.sin(f / 8);
  const BAR = 138; // letterbox 1920x804 ~ 2.39:1 (cinemascope)

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <Img src={srcSat(images[0])} style={{ width: 1920, height: 1080, objectFit: "cover", transform: `scale(${zoom})`, transformOrigin: "35% 50%", filter: "saturate(0.94) contrast(1.04)" }} />
      {/* painel lateral direito: gradiente escuro com texto + mapa */}
      <AbsoluteFill style={{ background: "linear-gradient(to left, rgba(6,9,15,0.95) 0%, rgba(6,9,15,0.88) 26%, rgba(6,9,15,0.45) 38%, transparent 52%)", opacity: painel }} />
      <div style={{ position: "absolute", top: BAR + 44, bottom: BAR + 36, right: 64, width: MW, display: "flex", flexDirection: "column", opacity: painel, transform: `translateX(${(1 - painel) * 60}px)` }}>
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 24, color: accent, letterSpacing: 7, opacity: txt1 }}>{(kicker || "ON LOCATION").toUpperCase()}</div>
        <div style={{ fontFamily: DISPLAY, fontSize: 74, color: "#fff", lineHeight: 1.04, marginTop: 10, textShadow: "0 4px 24px rgba(0,0,0,0.8)", opacity: txt1, transform: `translateY(${(1 - txt1) * 18}px)` }}>{nome}</div>
        {titulo && nome !== titulo ? <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 29, color: "#c9d2e0", marginTop: 10, opacity: txt2 }}>{titulo}</div> : null}
        <div style={{ width: 110, height: 5, background: accent, borderRadius: 3, marginTop: 18, boxShadow: `0 0 16px ${accent}`, opacity: txt2 }} />
        {/* o MAPA — parte da imagem: país/região com pin do lugar */}
        <svg width={MW} height={MH} style={{ marginTop: "auto", opacity: mapa }}>
          {alvo ? (
            <>
              {FEATURES.map((ft, i) => (
                <path key={i} d={path(ft) || undefined} fill={ft === alvo ? "#232e42" : "#141b28"} stroke={ft === alvo ? accent : TRACO} strokeWidth={ft === alvo ? 2.2 : 0.6} opacity={ft === alvo ? 1 : 0.55} style={ft === alvo ? { filter: `drop-shadow(0 0 12px ${accent}66)` } : undefined} />
              ))}
            </>
          ) : (
            FEATURES.map((ft, i) => <path key={i} d={path(ft) || undefined} fill="#141b28" stroke={TRACO} strokeWidth={0.6} opacity={0.55} />)
          )}
          {pin ? (
            <g>
              <circle cx={pin[0]} cy={pin[1]} r={9 + 7 * pulse} fill="none" stroke={accent} strokeWidth={2.5} opacity={0.85} />
              <circle cx={pin[0]} cy={pin[1]} r={6} fill={accent} style={{ filter: `drop-shadow(0 0 10px ${accent})` }} />
              <circle cx={pin[0]} cy={pin[1]} r={2.5} fill="#fff" />
            </g>
          ) : null}
        </svg>
        {g.temPonto ? (
          <div style={{ fontFamily: MONO, fontSize: 19, color: "#7d94b8", marginTop: 12, opacity: mapa }}>
            {Math.abs(g.pontosOk[0].lat).toFixed(2)}°{g.pontosOk[0].lat >= 0 ? "N" : "S"} · {Math.abs(g.pontosOk[0].lon).toFixed(2)}°{g.pontosOk[0].lon >= 0 ? "E" : "W"}
          </div>
        ) : null}
      </div>
      {/* LETTERBOX — faixas pretas cinematográficas (por cima de tudo) */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: BAR, background: "#000", transform: `translateY(${(bar - 1) * BAR}px)` }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: BAR, background: "#000", transform: `translateY(${(1 - bar) * BAR}px)` }} />
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO ---------------- */
export const MAPAS_MANIFEST = [
  { id: 0, comp: "Map01_CountryFocus", precisa: "1 país", quando: "citar UM país/nação" },
  { id: 1, comp: "Map02_MultiHighlight", precisa: "2+ países", quando: "vários países citados (valores SÓ se ancorados)" },
  { id: 2, comp: "Map03_RouteArc", precisa: "2 pontos lat/lon", quando: "rota/ligação A→B (fábrica→mercado)" },
  { id: 3, comp: "Map04_PinCallout", precisa: "1 ponto lat/lon", quando: "local específico (cidade/base/planta)" },
  { id: 4, comp: "Map05_RegionZoom", precisa: "1 país", quando: "mergulho cinematográfico mundo→país" },
  { id: 5, comp: "Map06_PathTrail", precisa: "3+ pontos", quando: "expedição/jornada multi-parada" },
  { id: 6, comp: "Map07_RadarSweep", precisa: "1 ponto", quando: "zona de operação/conflito/vigilância" },
  { id: 7, comp: "Map08_StatMap", precisa: "1 país + 1 valor", quando: "país + dado ancorado (mapa+stat)" },
  { id: 8, comp: "Map09_EarthZoom", precisa: "1 ponto + pilha sat (3-6 níveis)", sat: "imagery", quando: "mergulho Google-Earth do espaço até o local exato" },
  { id: 9, comp: "Map10_SatPinApp", precisa: "1 ponto + 1 sat próximo", sat: "imagery", quando: "mostrar o LOCAL real de cima (planta/cidade/base) estilo app de mapas" },
  { id: 10, comp: "Map11_StreetRoute", precisa: "2 pontos + mapa de ruas + bbox", sat: "street", quando: "trajeto urbano/regional A→B estilo navegação (km real calculado)" },
  { id: 11, comp: "Map12_SatTarget", precisa: "1 ponto + 1 sat médio", sat: "imagery", quando: "zona/instalação com vibe recon militar (brackets + HUD)" },
  { id: 12, comp: "Map13_CineLocation", precisa: "1 foto + país/ponto", imgs: 1, quando: "apresentar um LUGAR: foto cinematográfica (letterbox) + mapa lateral + nome" },
];

export const MAPAS_COMPS: Record<string, React.FC<P>> = {
  Map01_CountryFocus, Map02_MultiHighlight, Map03_RouteArc, Map04_PinCallout,
  Map05_RegionZoom, Map06_PathTrail, Map07_RadarSweep, Map08_StatMap,
  Map09_EarthZoom, Map10_SatPinApp, Map11_StreetRoute, Map12_SatTarget, Map13_CineLocation,
};
