import {
  AbsoluteFill, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath, geoBounds } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// REGION LOCATION TEXT — mapa-mundi vetorial real com o `countryName` DESTACADO (accent), enquadrado
// no país; label GRANDE (text) entrando + subtítulo (regionName). Container VidMator, niche-agnostic.
const W = 1920, H = 1080;
const BASE_FILL = "#151b29", BASE_STROKE = "#26314a";
const SANS = "'Inter','Segoe UI',sans-serif";

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

const ALIASES: Record<string, string> = {
  "united states": "United States of America", "usa": "United States of America",
  "u.s.": "United States of America", "us": "United States of America", "america": "United States of America",
  "uk": "United Kingdom", "u.k.": "United Kingdom", "england": "United Kingdom",
  "britain": "United Kingdom", "great britain": "United Kingdom",
  "uae": "United Arab Emirates", "emirates": "United Arab Emirates",
  "persia": "Iran", "czech republic": "Czechia", "ivory coast": "Côte d'Ivoire",
  "south korea": "South Korea", "north korea": "North Korea",
};

function findCountry(name?: string): any | null {
  if (!name) return null;
  const q = name.trim().toLowerCase();
  const target = (ALIASES[q] || name).toLowerCase();
  let f = features.find((x) => (x.properties?.name || "").toLowerCase() === target);
  if (!f) f = features.find((x) => (x.properties?.name || "").toLowerCase().includes(target));
  return f || null;
}

function makeProjection(
  feats: any[], box: [[number, number], [number, number]],
  fallback: { center: [number, number]; scale: number }, maxScale: number,
): any {
  const proj = geoMercator();
  const valid = feats.filter(Boolean);
  const boxCx = (box[0][0] + box[1][0]) / 2, boxCy = (box[0][1] + box[1][1]) / 2;
  if (valid.length) {
    const fc = { type: "FeatureCollection", features: valid } as any;
    proj.fitExtent(box, fc);
    if (!isFinite(proj.scale()) || proj.scale() > maxScale) {
      let center = fallback.center;
      try { const b = geoBounds(fc); center = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]; } catch {}
      proj.scale(maxScale).center(center).translate([boxCx, boxCy]);
    }
  } else {
    proj.center(fallback.center).scale(fallback.scale).translate([boxCx, boxCy]);
  }
  return proj;
}

export const RegionLocationText: React.FC<{
  countryName?: string;
  regionName?: string;
  text?: string;
  accent?: string;
}> = ({
  countryName = "United States",
  regionName = "California",
  text = "California | USA",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const target = findCountry(countryName);
  const proj = makeProjection(target ? [target] : [], [[220, 120], [W - 220, H - 120]], { center: [0, 25], scale: 220 }, 2600);
  const path = geoPath(proj as any);

  const hl = interpolate(frame, [8, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tagIn = spring({ frame: frame - 14, fps, config: { damping: 14 }, durationInFrames: 18 });
  const bigIn = spring({ frame: frame - 24, fps, config: { damping: 15, stiffness: 80 }, durationInFrames: 26 });
  const barW = interpolate(bigIn, [0, 1], [0, 340]);
  const regIn = interpolate(frame, [42, 58], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {features.map((f, i) => (
          <path key={i} d={path(f) || ""} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={0.7} />
        ))}
        {target && (
          <path d={path(target) || ""} fill={accent} fillOpacity={0.14 + 0.7 * hl} stroke={accent} strokeWidth={1.8} />
        )}
      </svg>

      {/* gradiente p/ legibilidade do texto */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,8,15,0.15) 0%, rgba(5,8,15,0.1) 45%, rgba(5,8,15,0.82) 100%)" }} />

      <div style={{ position: "absolute", left: 96, bottom: 150, fontFamily: SANS }}>
        <div style={{
          display: "inline-block", opacity: Math.min(1, tagIn), transform: `translateY(${(1 - tagIn) * 14}px)`,
          background: `${accent}1a`, border: `1px solid ${accent}`, borderRadius: 8, padding: "6px 16px",
          fontSize: 24, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", color: accent,
        }}>{countryName}</div>

        <div style={{
          fontFamily: SANS, fontSize: 132, fontWeight: 800, color: "#fff", lineHeight: 1.02, marginTop: 18,
          opacity: Math.min(1, bigIn), transform: `translateX(${(1 - bigIn) * -30}px)`,
          textShadow: "0 6px 30px rgba(0,0,0,0.85)", maxWidth: 1600,
        }}>{text}</div>

        <div style={{ height: 6, width: barW, background: accent, marginTop: 12, boxShadow: `0 0 20px ${accent}` }} />

        <div style={{
          fontSize: 34, fontWeight: 600, color: "#9aa4b2", marginTop: 18, letterSpacing: 1,
          opacity: regIn, transform: `translateY(${(1 - regIn) * 12}px)`,
        }}>{regionName}</div>
      </div>
    </AbsoluteFill>
  );
};
