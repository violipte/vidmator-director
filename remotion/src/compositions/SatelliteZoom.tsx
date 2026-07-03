import {
  AbsoluteFill, Img, staticFile, interpolate, spring, Easing,
  useCurrentFrame, useVideoConfig,
} from "remotion";

const W = 1920, H = 1080;
const ACCENT = "#34d399"; // verde "scanner" de satélite

type Nivel = { rel: string; half: number };
type Props = {
  niveis?: Nivel[];
  coord?: [number, number]; // [lng, lat] — pro HUD
  legenda?: string;
  durFrames?: number;
};

const DEFAULT_NIVEIS: Nivel[] = [
  { rel: "sat/giza_0.jpg", half: 1500000 },
  { rel: "sat/giza_1.jpg", half: 330000 },
  { rel: "sat/giza_2.jpg", half: 73000 },
  { rel: "sat/giza_3.jpg", half: 16000 },
  { rel: "sat/giza_4.jpg", half: 3600 },
  { rel: "sat/giza_5.jpg", half: 800 },
];

const smooth = (x: number, a: number, b: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export const SatelliteZoom: React.FC<Props> = ({
  niveis = DEFAULT_NIVEIS, coord = [31.1313, 29.9773], legenda = "Giza, Egypt", durFrames,
}) => {
  const frame = useCurrentFrame();
  const cfg = useVideoConfig();
  const fps = cfg.fps;
  const F = durFrames || cfg.durationInFrames;

  const us = niveis.map((n) => Math.log(n.half));
  const u0 = us[0], uLast = us[us.length - 1];

  // mergulho: logZ desce de u0 -> uLast na fase de zoom (0..85%), depois trava no alvo
  const zoomEnd = 0.84;
  const tz = smooth(frame / F, 0, zoomEnd); // ease in/out do mergulho
  const logZ = interpolate(tz, [0, 1], [u0, uLast]);

  // HUD de coordenadas "varre" enquanto desce, trava no alvo
  const settle = smooth(frame / F, zoomEnd - 0.1, zoomEnd + 0.02);
  const [lng, lat] = coord;
  const showLng = interpolate(settle, [0, 1], [lng - 6, lng]);
  const showLat = interpolate(settle, [0, 1], [lat + 6, lat]);

  // reticle + label aparecem no fim
  const lockIn = spring({ frame: frame - Math.round(F * zoomEnd), fps, config: { damping: 14 }, durationInFrames: 22 });
  const labelIn = spring({ frame: frame - Math.round(F * (zoomEnd + 0.03)), fps, config: { damping: 13 }, durationInFrames: 18 });

  return (
    <AbsoluteFill style={{ backgroundColor: "#04070d", overflow: "hidden" }}>
      {/* PILHA de satélite: coarse (fundo) -> fine (topo). O nível fino entra nítido quando cobre a tela */}
      {niveis.map((n, i) => {
        const scale = Math.exp(us[i] - logZ);
        const appear = i === 0 ? 1 : smooth(scale, 1.0, 1.4);
        const nextAppear = i < niveis.length - 1 ? smooth(Math.exp(us[i + 1] - logZ), 1.0, 1.4) : 0;
        const opacity = Math.max(0, Math.min(1, appear) * (1 - nextAppear));
        if (opacity < 0.003 || scale < 0.2) return null;
        return (
          <AbsoluteFill key={i} style={{ opacity }}>
            <Img src={staticFile(n.rel)} style={{
              width: W, height: H, objectFit: "cover",
              transform: `scale(${scale.toFixed(4)})`, transformOrigin: "center center",
            }} />
          </AbsoluteFill>
        );
      })}

      {/* leve grade + vinheta p/ casar com o look premium */}
      <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "soft-light", opacity: 0.35,
        background: "linear-gradient(160deg, #0b2a4a 0%, transparent 45%, #2a0f14 100%)" }} />
      <AbsoluteFill style={{ pointerEvents: "none",
        boxShadow: "inset 0 0 320px 90px rgba(0,0,0,0.75)" }} />

      {/* HUD canto superior esquerdo */}
      <div style={{ position: "absolute", top: 40, left: 48, fontFamily: "'Consolas','SF Mono',monospace",
        color: ACCENT, fontSize: 22, letterSpacing: 1, textShadow: "0 1px 6px rgba(0,0,0,0.9)", lineHeight: 1.7 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, opacity: 0.95 }}>
          <span style={{ width: 9, height: 9, borderRadius: "50%", background: ACCENT,
            opacity: 0.4 + 0.6 * Math.abs(Math.sin(frame / 7)), display: "inline-block" }} />
          SATELLITE · LIVE
        </div>
        <div>LAT {Math.abs(showLat).toFixed(4)}° {showLat >= 0 ? "N" : "S"}</div>
        <div>LON {Math.abs(showLng).toFixed(4)}° {showLng >= 0 ? "E" : "W"}</div>
      </div>

      {/* reticle (mira) que trava no alvo no centro */}
      {lockIn > 0.01 && (
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
          <g opacity={lockIn} transform={`translate(${W / 2} ${H / 2})`}>
            <circle r={54 + 30 * (1 - lockIn)} fill="none" stroke={ACCENT} strokeWidth={2} opacity={0.85} />
            <circle r={6} fill={ACCENT} />
            {[0, 90, 180, 270].map((a) => (
              <line key={a} transform={`rotate(${a})`} x1={0} y1={-40} x2={0} y2={-72}
                stroke={ACCENT} strokeWidth={2} />
            ))}
          </g>
        </svg>
      )}

      {/* label do alvo */}
      {labelIn > 0.01 && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 110, textAlign: "center",
          opacity: labelIn, transform: `translateY(${(1 - labelIn) * 20}px)` }}>
          <div style={{ display: "inline-block", padding: "12px 30px", borderRadius: 6,
            background: "rgba(4,10,18,0.62)", border: `1px solid ${ACCENT}`, backdropFilter: "blur(3px)",
            color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", fontWeight: 700, fontSize: 34,
            letterSpacing: 1, textShadow: "0 2px 12px rgba(0,0,0,0.9)" }}>
            {legenda}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
