import {
  AbsoluteFill, interpolate, spring, Easing,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// MAP ROUTE — mapa-mundi vetorial real enquadrado na região dos 2 pontos; pins start/end (via proj)
// + ARCO curvo (quadrático) DESENHADO entre eles (stroke-dashoffset) + marcador viajante + labels.
// Container VidMator, niche-agnostic.
const W = 1920, H = 1080;
const BASE_FILL = "#151b29", BASE_STROKE = "#26314a";
const SANS = "'Inter','Segoe UI',sans-serif";

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

const bez = (t: number, a: number, c: number, b: number) => (1 - t) * (1 - t) * a + 2 * (1 - t) * t * c + t * t * b;
function quadLen(p0: number[], cp: number[], p2: number[]): number {
  let len = 0, px = p0[0], py = p0[1];
  for (let i = 1; i <= 64; i++) {
    const t = i / 64, x = bez(t, p0[0], cp[0], p2[0]), y = bez(t, p0[1], cp[1], p2[1]);
    len += Math.hypot(x - px, y - py); px = x; py = y;
  }
  return len;
}

export const MapRoute: React.FC<{
  startName?: string;
  startCoord?: [number, number];
  endName?: string;
  endCoord?: [number, number];
  accent?: string;
}> = ({
  startName = "Tehran",
  startCoord = [51.4, 35.7],
  endName = "Dubai",
  endCoord = [55.3, 25.2],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sc: [number, number] = [Number(startCoord[0]), Number(startCoord[1])];
  const ec: [number, number] = [Number(endCoord[0]), Number(endCoord[1])];
  const midLng = (sc[0] + ec[0]) / 2, midLat = (sc[1] + ec[1]) / 2;

  const box: [[number, number], [number, number]] = [[560, 260], [W - 560, H - 280]];
  const proj = geoMercator();
  try {
    proj.fitExtent(box, { type: "MultiPoint", coordinates: [sc, ec] } as any);
    if (!isFinite(proj.scale()) || proj.scale() > 9000) throw new Error("degenerate");
  } catch {
    proj.center([midLng, midLat]).scale(1400).translate([W / 2, H / 2]);
  }
  const path = geoPath(proj as any);

  const s = proj(sc) || [560, 540];
  const e = proj(ec) || [1360, 540];
  const dist = Math.hypot(e[0] - s[0], e[1] - s[1]);
  const lift = Math.min(300, Math.max(120, dist * 0.34));
  const cp: [number, number] = [(s[0] + e[0]) / 2, Math.min(s[1], e[1]) - lift];
  const D = `M ${s[0]} ${s[1]} Q ${cp[0]} ${cp[1]} ${e[0]} ${e[1]}`;
  const LEN = quadLen(s, cp, e);

  const bgOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const startPin = spring({ frame: frame - 14, fps, config: { damping: 12 }, durationInFrames: 16 });
  const endPin = spring({ frame: frame - 26, fps, config: { damping: 12 }, durationInFrames: 16 });

  const draw = interpolate(frame, [36, 112], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const dashOffset = LEN * (1 - draw);
  const headX = bez(draw, s[0], cp[0], e[0]), headY = bez(draw, s[1], cp[1], e[1]);
  const pulseA = ((frame - 14) % 44) / 44, pulseB = ((frame - 26) % 44) / 44;

  const pin = (x: number, y: number, app: number, pulse: number) => (
    <g opacity={Math.min(1, app)}>
      <circle cx={x} cy={y} r={10 + 22 * pulse} fill="none" stroke={accent} strokeWidth={2} opacity={(1 - pulse) * app} />
      <g transform={`translate(0 ${interpolate(app, [0, 1], [-40, 0])})`}>
        <line x1={x} y1={y} x2={x} y2={y - 42} stroke={accent} strokeWidth={3} opacity={0.85} />
        <circle cx={x} cy={y - 48} r={12} fill={accent} stroke="#fff" strokeWidth={2} />
      </g>
      <circle cx={x} cy={y} r={5} fill="#fff" />
    </g>
  );

  const label = (x: number, y: number, name: string, app: number) => (
    <div style={{
      position: "absolute", left: x - 100, top: y + 16, width: 200, textAlign: "center",
      opacity: Math.min(1, app), transform: `translateY(${(1 - app) * 12}px)`,
    }}>
      <div style={{
        display: "inline-block", background: "#14161c", border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 10, boxShadow: "0 16px 44px rgba(0,0,0,0.6)", padding: "8px 18px",
        fontFamily: SANS, fontSize: 28, fontWeight: 700, color: "#fff", letterSpacing: 0.5,
      }}>{name}</div>
    </div>
  );

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ opacity: bgOp }}>
        {features.map((f, i) => (
          <path key={i} d={path(f) || ""} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={0.6} />
        ))}
        {/* trilho base */}
        <path d={D} fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth={3} strokeDasharray="2 10" strokeLinecap="round" />
        {/* glow */}
        <path d={D} fill="none" stroke={accent} strokeWidth={10} opacity={0.3} strokeLinecap="round"
          style={{ filter: "blur(6px)", strokeDasharray: LEN, strokeDashoffset: dashOffset }} />
        {/* arco principal */}
        <path d={D} fill="none" stroke={accent} strokeWidth={4.5} strokeLinecap="round"
          style={{ strokeDasharray: LEN, strokeDashoffset: dashOffset }} />
        {draw > 0.01 && draw < 0.999 && (
          <circle cx={headX} cy={headY} r={8} fill="#fff" stroke={accent} strokeWidth={3} />
        )}
        {pin(s[0], s[1], startPin, pulseA)}
        {pin(e[0], e[1], endPin, pulseB)}
      </svg>

      {label(s[0], s[1], startName, startPin)}
      {label(e[0], e[1], endName, endPin)}
    </AbsoluteFill>
  );
};
