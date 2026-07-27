import {
  AbsoluteFill, interpolate, spring, Easing,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// SATELLITE DRAW PATH — mapa-mundi vetorial real ZOOMADO em centerCoord; uma ROTA/trajetória curva
// é DESENHADA (stroke-dashoffset) atravessando a área; label do local em CAIXA-ALTA embaixo à esquerda.
// Vibe de "traçar rota no mapa". Container VidMator, niche-agnostic.
const W = 1920, H = 1080;
const BASE_FILL = "#151b29", BASE_STROKE = "#26314a";
const SANS = "'Inter','Segoe UI',sans-serif";
const MONO = "'Consolas','SF Mono',monospace";

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

// rota curva atravessando o quadro (screen-space, passa pela região central)
const PATH_D = "M 300 800 C 620 640, 780 470, 980 500 S 1420 560, 1660 340";
const PATH_LEN = 1950;

export const SatelliteDrawPath: React.FC<{
  locationLabel?: string;
  centerCoord?: [number, number];
  accent?: string;
}> = ({
  locationLabel = "Fada, Chad — 1986",
  centerCoord = [19, 17],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const cc: [number, number] = [Number(centerCoord[0]), Number(centerCoord[1])];

  const scale = interpolate(frame, [0, durationInFrames], [1600, 2050], { extrapolateRight: "clamp" });
  const proj = geoMercator().center(cc).scale(scale).translate([W / 2, H / 2]);
  const path = geoPath(proj as any);

  const bgOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const draw = interpolate(frame, [22, 104], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const dashOffset = PATH_LEN * (1 - draw);
  const dotIn = spring({ frame: frame - 16, fps, config: { damping: 13 }, durationInFrames: 16 });
  const labelIn = spring({ frame: frame - 20, fps, config: { damping: 14 }, durationInFrames: 20 });
  const hudPulse = 0.4 + 0.6 * Math.abs(Math.sin(frame / 8));

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ opacity: bgOp }}>
        {features.map((f, i) => (
          <path key={i} d={path(f) || ""} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={0.7} />
        ))}

        {/* trilho base fraco */}
        <path d={PATH_D} fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth={4} strokeDasharray="2 10" strokeLinecap="round" />
        {/* glow */}
        <path d={PATH_D} fill="none" stroke={accent} strokeWidth={10} strokeLinecap="round" opacity={0.35}
          style={{ filter: "blur(6px)", strokeDasharray: PATH_LEN, strokeDashoffset: dashOffset }} />
        {/* traço principal */}
        <path d={PATH_D} fill="none" stroke={accent} strokeWidth={4.5} strokeLinecap="round"
          style={{ strokeDasharray: PATH_LEN, strokeDashoffset: dashOffset }} />
        {/* origem */}
        <circle cx={300} cy={800} r={9 * dotIn} fill="#fff" stroke={accent} strokeWidth={3} />
        {/* destino (aparece ao terminar o traço) */}
        {draw > 0.98 && <circle cx={1660} cy={340} r={9} fill={accent} stroke="#fff" strokeWidth={3} />}
      </svg>

      {/* HUD canto sup. esq. */}
      <div style={{ position: "absolute", top: 40, left: 48, fontFamily: MONO, color: accent, fontSize: 20, letterSpacing: 1, textShadow: "0 1px 6px rgba(0,0,0,0.9)" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 9, height: 9, borderRadius: "50%", background: accent, opacity: hudPulse }} />
          RECON · TRACKING
        </span>
      </div>

      {/* label — CAIXA-ALTA, canto inferior esquerdo */}
      <div style={{ position: "absolute", left: 56, bottom: 64, opacity: Math.min(1, labelIn), transform: `translateY(${(1 - labelIn) * 16}px)` }}>
        <div style={{ width: 46, height: 4, background: accent, marginBottom: 14, boxShadow: `0 0 16px ${accent}` }} />
        <div style={{
          fontFamily: SANS, fontSize: 44, fontWeight: 800, color: "#fff",
          textTransform: "uppercase", letterSpacing: 2, textShadow: "0 3px 18px rgba(0,0,0,0.9)",
        }}>{locationLabel}</div>
      </div>
    </AbsoluteFill>
  );
};
