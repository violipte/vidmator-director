import {
  AbsoluteFill, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// SATELLITE LOCATION PIN — mapa-mundi vetorial real ZOOMADO no ponto [longitude,latitude];
// um PIN cai no centro (spring) com anel pulsante + reticle/mira; card com nome + subtítulo + coords
// (fonte mono); HUD "SATELLITE · LIVE" no topo. Container VidMator, niche-agnostic.
const W = 1920, H = 1080;
const BASE_FILL = "#151b29", BASE_STROKE = "#26314a";
const SANS = "'Inter','Segoe UI',sans-serif";
const MONO = "'Consolas','SF Mono',monospace";

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

export const SatelliteLocationPin: React.FC<{
  longitude?: number;
  latitude?: number;
  locationName?: string;
  locationSubTitle?: string;
  accent?: string;
}> = ({
  longitude = 55.3,
  latitude = 25.2,
  locationName = "Dubai",
  locationSubTitle = "2025",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const lon = Number(longitude), lat = Number(latitude);

  // zoom lento sobre o ponto
  const scale = interpolate(frame, [0, durationInFrames], [1900, 2600], { extrapolateRight: "clamp" });
  const proj = geoMercator().center([lon, lat]).scale(scale).translate([W / 2, H / 2]);
  const path = geoPath(proj as any);
  const CX = W / 2, CY = H / 2;

  // pin cai do topo com bounce
  const drop = spring({ frame: frame - 18, fps, config: { damping: 11, stiffness: 120, mass: 1 }, durationInFrames: 26 });
  const pinY = interpolate(drop, [0, 1], [-340, 0]);
  const pinOp = interpolate(frame, [18, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const impact = interpolate(frame, [40, 44, 62], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const shadowScale = interpolate(drop, [0, 1], [0.3, 1]);
  const ring = ((frame - 44) % 46) / 46;

  const lockIn = spring({ frame: frame - 42, fps, config: { damping: 14 }, durationInFrames: 22 });
  const cardIn = spring({ frame: frame - 48, fps, config: { damping: 14 }, durationInFrames: 20 });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {features.map((f, i) => (
          <path key={i} d={path(f) || ""} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={0.7} />
        ))}

        {/* onda de impacto + anel pulsante */}
        {impact > 0.001 && (
          <circle cx={CX} cy={CY} r={14 + 78 * impact} fill="none" stroke={accent} strokeWidth={3} opacity={(1 - impact) * 0.9} />
        )}
        {frame > 44 && (
          <circle cx={CX} cy={CY} r={20 + 40 * ring} fill="none" stroke={accent} strokeWidth={2} opacity={(1 - ring) * 0.7} />
        )}

        {/* reticle / mira */}
        {lockIn > 0.01 && (
          <g opacity={lockIn} transform={`translate(${CX} ${CY})`}>
            <circle r={58 + 30 * (1 - lockIn)} fill="none" stroke={accent} strokeWidth={2} opacity={0.85} />
            {[0, 90, 180, 270].map((a) => (
              <line key={a} transform={`rotate(${a})`} x1={0} y1={-44} x2={0} y2={-78} stroke={accent} strokeWidth={2} />
            ))}
          </g>
        )}

        {/* sombra + PIN teardrop */}
        <ellipse cx={CX} cy={CY} rx={34 * shadowScale} ry={11 * shadowScale} fill="rgba(0,0,0,0.55)" opacity={pinOp} />
        <g transform={`translate(${CX} ${CY + pinY})`} opacity={pinOp}>
          <path d="M 0 0 C -26 -34, -26 -78, 0 -96 C 26 -78, 26 -34, 0 0 Z" fill={accent} stroke="#fff" strokeWidth={3}
            style={{ filter: "drop-shadow(0 8px 14px rgba(0,0,0,0.6))" }} />
          <circle cx={0} cy={-64} r={13} fill="#fff" />
        </g>
      </svg>

      {/* HUD topo esquerdo */}
      <div style={{ position: "absolute", top: 40, left: 48, fontFamily: MONO, color: accent, fontSize: 22, letterSpacing: 1, textShadow: "0 1px 6px rgba(0,0,0,0.9)" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 9, height: 9, borderRadius: "50%", background: accent, opacity: 0.4 + 0.6 * Math.abs(Math.sin(frame / 7)) }} />
          SATELLITE · LIVE
        </span>
      </div>

      {/* card canto inferior direito */}
      <div style={{
        position: "absolute", right: 64, bottom: 90, textAlign: "right",
        opacity: Math.min(1, cardIn), transform: `translateY(${(1 - cardIn) * 24}px)`,
      }}>
        <div style={{
          display: "inline-block", background: "rgba(20,22,28,0.92)", border: `1px solid ${accent}`,
          borderRadius: 14, boxShadow: "0 20px 60px rgba(0,0,0,0.6)", padding: "18px 40px", backdropFilter: "blur(3px)",
        }}>
          <div style={{ fontFamily: SANS, fontSize: 60, fontWeight: 800, color: "#fff", lineHeight: 1, letterSpacing: 0.5 }}>{locationName}</div>
          <div style={{ fontFamily: SANS, fontSize: 28, fontWeight: 700, color: accent, marginTop: 8, letterSpacing: 1.5, textTransform: "uppercase", textShadow: `0 0 20px ${accent}55` }}>{locationSubTitle}</div>
          <div style={{ fontFamily: MONO, fontSize: 20, color: "#9aa4b2", marginTop: 12, letterSpacing: 1 }}>
            {Math.abs(lat).toFixed(4)}° {lat >= 0 ? "N" : "S"} · {Math.abs(lon).toFixed(4)}° {lon >= 0 ? "E" : "W"}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
