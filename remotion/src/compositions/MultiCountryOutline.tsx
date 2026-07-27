import {
  AbsoluteFill, interpolate, spring, Easing,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath, geoCentroid, geoBounds } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// MULTI COUNTRY OUTLINE — mapa-mundi vetorial real (d3-geo + world-atlas), enquadrado na Europa.
// Cada país da lista é DESTACADO (fill accent) casando f.properties.name; pin no centroide + card
// (nome + valor) entrando em sequência (spring escalonado). Container VidMator, niche-agnostic.
const W = 1920, H = 1080;
const BASE_FILL = "#151b29", BASE_STROKE = "#26314a";
const SANS = "'Inter','Segoe UI',sans-serif";

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

// aliases p/ nomes que diferem do world-atlas (ex.: "United States" -> "United States of America")
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

// projeção que enquadra os países alvo dentro de `box` (fallback seguro se nada for achado)
function makeProjection(
  feats: any[], box: [[number, number], [number, number]],
  fallback: { center: [number, number]; scale: number }, maxScale = 4200,
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
      proj.scale(Math.min(maxScale, fallback.scale * 3)).center(center).translate([boxCx, boxCy]);
    }
  } else {
    proj.center(fallback.center).scale(fallback.scale).translate([boxCx, boxCy]);
  }
  return proj;
}

export const MultiCountryOutline: React.FC<{
  countries?: string[];
  values?: string[];
  accent?: string;
}> = ({
  countries = ["United Kingdom", "Germany", "Portugal"],
  values = ["+1.3%", "+0.4%", "+1.9%"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const targets = countries.map((c) => findCountry(c));
  const proj = makeProjection(targets, [[150, 160], [1360, H - 160]], { center: [10, 50], scale: 700 });
  const path = geoPath(proj as any);

  // coluna de cards à direita (robusta p/ qualquer nº de países)
  const cardX = 1440, cardW = 400, gap = 156;
  const stackTop = Math.max(120, (H - countries.length * gap) / 2);

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {features.map((f, i) => (
          <path key={i} d={path(f) || ""} fill={BASE_FILL} stroke={BASE_STROKE} strokeWidth={0.6} />
        ))}
        {targets.map((f, i) => {
          if (!f) return null;
          const startF = 14 + i * 16;
          const hl = interpolate(frame, [startF, startF + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const app = spring({ frame: frame - startF, fps, config: { damping: 13, stiffness: 90 }, durationInFrames: 20 });
          const pin = proj(geoCentroid(f) as [number, number]);
          const pulse = ((frame - startF) % 42) / 42;
          const cardCy = stackTop + i * gap + gap / 2;
          const lp = interpolate(frame, [startF + 6, startF + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          return (
            <g key={"h" + i}>
              <path d={path(f) || ""} fill={accent} fillOpacity={0.12 + 0.72 * hl} stroke={accent} strokeWidth={1.6} />
              {pin && (
                <>
                  {lp > 0 && (
                    <line x1={pin[0]} y1={pin[1]} x2={pin[0] + (cardX - pin[0]) * lp} y2={pin[1] + (cardCy - pin[1]) * lp}
                      stroke={accent} strokeWidth={2} strokeDasharray="8 6" opacity={0.65 * app} />
                  )}
                  {app > 0.001 && (
                    <g>
                      <circle cx={pin[0]} cy={pin[1]} r={7 + 15 * pulse} fill="none" stroke={accent} strokeWidth={2} opacity={(1 - pulse) * app} />
                      <circle cx={pin[0]} cy={pin[1]} r={6 * app} fill={accent} stroke="#fff" strokeWidth={1.5} />
                    </g>
                  )}
                </>
              )}
            </g>
          );
        })}
      </svg>

      {countries.map((c, i) => {
        const startF = 14 + i * 16;
        const app = spring({ frame: frame - (startF + 6), fps, config: { damping: 14, stiffness: 80 }, durationInFrames: 20 });
        if (app <= 0.001) return null;
        const cardCy = stackTop + i * gap + gap / 2;
        return (
          <div key={i} style={{
            position: "absolute", left: cardX, top: cardCy - 46, width: cardW,
            opacity: Math.min(1, app), transform: `translateX(${(1 - app) * 24}px)`,
          }}>
            <div style={{
              background: "#14161c", border: "1px solid rgba(255,255,255,0.08)",
              borderLeft: `4px solid ${accent}`, borderRadius: 12,
              boxShadow: "0 20px 60px rgba(0,0,0,0.6)", padding: "12px 22px",
            }}>
              <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 700, color: "#fff", letterSpacing: 0.4 }}>{c}</div>
              <div style={{ fontFamily: SANS, fontSize: 40, fontWeight: 800, color: accent, lineHeight: 1.05, textShadow: `0 0 22px ${accent}66` }}>{values[i] || ""}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
