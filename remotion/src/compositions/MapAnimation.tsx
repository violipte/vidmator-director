import {
  AbsoluteFill, Img, staticFile, interpolate, spring, Easing,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { geoMercator, geoPath, geoCentroid } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-110m.json";

const ACCENT = "#e0452e";
const W = 1920, H = 1080;

const geo: any = feature(world as any, (world as any).objects.countries);
const features: any[] = geo.features;

type Props = {
  pais?: string;
  coord?: [number, number];   // [lng, lat] do pin
  legenda?: string;
  imagem_rel?: string;
  durFrames?: number;         // duração do segmento (escala o timing); default = composição
};

export const MapAnimation: React.FC<Props> = ({
  pais = "Egypt", coord = [31.24, 30.04], legenda = "Ancient Egypt", imagem_rel = "test/map_img.jpg",
  durFrames,
}) => {
  const frame = useCurrentFrame();
  const cfg = useVideoConfig();
  const fps = cfg.fps;
  const F = durFrames || cfg.durationInFrames; // total de frames deste segmento
  const at = (frac: number) => Math.round(frac * F); // keyframe relativo à duração

  const target = features.find((f) => (f.properties?.name || "").toLowerCase() === pais.toLowerCase());
  const centroid = target ? (geoCentroid(target) as [number, number]) : coord;

  // câmera: mundo -> país (zoom + pan com easing) — keyframes proporcionais à duração
  const zt = interpolate(frame, [at(0.15), at(0.49)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const scale = interpolate(zt, [0, 1], [230, 1500]);
  const cx = interpolate(zt, [0, 1], [14, centroid[0]]);
  const cy = interpolate(zt, [0, 1], [30, centroid[1]]);
  const proj = geoMercator().scale(scale).center([cx, cy]).translate([W / 2, H / 2]);
  const path = geoPath(proj);

  const hl = interpolate(frame, [at(0.47), at(0.57)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pin = proj(coord);
  const pinAppear = spring({ frame: frame - at(0.57), fps, config: { damping: 12 }, durationInFrames: 16 });
  const pulse = (frame % 40) / 40; // anel pulsando

  // linha tracejada cresce do pin até o card
  const cardCX = W * 0.70, cardTop = H * 0.14;
  const lineP = interpolate(frame, [at(0.62), at(0.76)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const lx2 = pin ? pin[0] + (cardCX - pin[0]) * lineP : 0;
  const ly2 = pin ? pin[1] + (cardTop + 170 - pin[1]) * lineP : 0;

  const cardAppear = spring({ frame: frame - at(0.71), fps, config: { damping: 13 }, durationInFrames: 18 });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #0b1320 0%, #05080f 100%)" }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {features.map((f, i) => {
          const isT = f === target;
          return (
            <path key={i} d={path(f) || ""}
              fill={isT ? `rgba(224,69,46,${0.12 + 0.78 * hl})` : "#151b29"}
              stroke={isT ? ACCENT : "#26314a"} strokeWidth={isT ? 1.4 : 0.5} />
          );
        })}
        {/* linha tracejada pin -> card */}
        {pin && lineP > 0 && (
          <line x1={pin[0]} y1={pin[1]} x2={lx2} y2={ly2} stroke="#ffffff" strokeWidth={2}
            strokeDasharray="9 6" opacity={0.85} />
        )}
        {/* pin pulsante */}
        {pin && pinAppear > 0 && (
          <g>
            <circle cx={pin[0]} cy={pin[1]} r={7 + 16 * pulse} fill="none" stroke={ACCENT} strokeWidth={2} opacity={(1 - pulse) * pinAppear} />
            <circle cx={pin[0]} cy={pin[1]} r={7 * pinAppear} fill={ACCENT} stroke="#fff" strokeWidth={1.5} />
          </g>
        )}
      </svg>

      {/* card de imagem (popup) */}
      {cardAppear > 0 && (
        <div style={{
          position: "absolute", left: cardCX - 150, top: cardTop, width: 300,
          opacity: cardAppear, transform: `scale(${0.82 + 0.18 * cardAppear})`,
        }}>
          <Img src={staticFile(imagem_rel)} style={{
            width: "100%", height: 180, objectFit: "cover", borderRadius: 6,
            border: "3px solid #ffffff", boxShadow: "0 10px 36px rgba(0,0,0,0.7)",
          }} />
          <div style={{
            textAlign: "center", color: "#fff", fontFamily: "'Segoe UI', system-ui, sans-serif",
            fontWeight: 700, fontSize: 26, marginTop: 10, letterSpacing: 0.5,
            textShadow: "0 2px 12px rgba(0,0,0,0.9)",
          }}>{legenda}</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
