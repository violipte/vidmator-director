import {
  AbsoluteFill, Img, staticFile, interpolate, spring,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath, geoBounds } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

// COUNTRY CHARACTER MAP — mapa-mundi vetorial real com o `countryName` DESTACADO/enquadrado; de um
// lado o recorte do personagem (Img com alpha), do outro name + title. Container VidMator, niche-agnostic.
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

export const CountryCharacterMap: React.FC<{
  countryName?: string;
  name?: string;
  title?: string;
  characterImage?: string;
  accent?: string;
}> = ({
  countryName = "United Kingdom",
  name = "Elizabeth I",
  title = "Queen of England",
  characterImage = "test/people/pessoa_1.png",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const target = findCountry(countryName);
  // enquadra o país no lado direito (deixa a esquerda p/ o personagem)
  const proj = makeProjection(target ? [target] : [], [[760, 170], [W - 160, H - 170]], { center: [10, 40], scale: 260 }, 3200);
  const path = geoPath(proj as any);

  const hl = interpolate(frame, [8, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const charIn = spring({ frame: frame - 12, fps, config: { damping: 15, stiffness: 70 }, durationInFrames: 26 });
  const charX = interpolate(charIn, [0, 1], [-140, 0]);
  const tagIn = spring({ frame: frame - 28, fps, config: { damping: 14 }, durationInFrames: 18 });
  const nameIn = spring({ frame: frame - 36, fps, config: { damping: 15, stiffness: 80 }, durationInFrames: 22 });
  const barW = interpolate(nameIn, [0, 1], [0, 300]);
  const titleIn = interpolate(frame, [52, 68], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

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

      {/* escurece p/ destacar personagem/texto */}
      <AbsoluteFill style={{ background: `radial-gradient(120% 110% at 28% 55%, rgba(5,8,15,0.55) 0%, transparent 42%), linear-gradient(90deg, rgba(4,5,9,0.7) 0%, rgba(6,8,14,0.25) 42%, rgba(4,5,9,0.55) 100%)` }} />

      {/* personagem — lado esquerdo */}
      <div style={{ position: "absolute", left: 120, bottom: 0, height: "94%", opacity: Math.min(1, charIn), transform: `translateX(${charX}px)` }}>
        <div style={{
          position: "absolute", left: "50%", bottom: "8%", width: 520, height: 520, transform: "translateX(-50%)",
          borderRadius: "50%", background: `radial-gradient(circle, ${accent}33 0%, transparent 66%)`, filter: "blur(10px)",
        }} />
        <Img src={staticFile(characterImage)} style={{
          position: "relative", height: "100%", objectFit: "contain",
          filter: "drop-shadow(0 18px 40px rgba(0,0,0,0.7))",
        }} />
      </div>

      {/* name / title — lado direito */}
      <div style={{ position: "absolute", right: 110, top: "50%", transform: "translateY(-50%)", textAlign: "right", fontFamily: SANS, maxWidth: 820 }}>
        <div style={{
          display: "inline-block", opacity: Math.min(1, tagIn), transform: `translateY(${(1 - tagIn) * 12}px)`,
          background: `${accent}1a`, border: `1px solid ${accent}`, borderRadius: 8, padding: "6px 16px",
          fontSize: 24, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase", color: accent,
        }}>{countryName}</div>

        <div style={{
          fontFamily: SANS, fontSize: 104, fontWeight: 800, color: "#fff", lineHeight: 1.02, marginTop: 20,
          opacity: Math.min(1, nameIn), transform: `translateX(${(1 - nameIn) * 30}px)`, textShadow: "0 6px 30px rgba(0,0,0,0.85)",
        }}>{name}</div>

        <div style={{ height: 6, width: barW, background: accent, margin: "16px 0 16px auto", boxShadow: `0 0 20px ${accent}` }} />

        <div style={{
          fontSize: 38, fontWeight: 600, color: "#9aa4b2", letterSpacing: 1,
          opacity: titleIn, transform: `translateY(${(1 - titleIn) * 12}px)`,
        }}>{title}</div>
      </div>
    </AbsoluteFill>
  );
};
