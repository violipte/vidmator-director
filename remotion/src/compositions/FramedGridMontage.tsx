import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

/* ============================================================
   FRAMED GRID MONTAGE — máscara "quadro + grid em perspectiva" que
   TAMBÉM é um container de montagem: N sub-clipes curtos (1–2s) trocam
   em CORTE SECO dentro da MESMA moldura fixa, sobre um fundo de malha
   curvada (barrel). Ref. VidRush (ex. Piter 2026-07-16 — Hilux Top Gear).
   - 2º estilo do StandardClip (alternativa ao blur-bg-fill).
   - Vídeo SEMPRE mudo (regra de áudio 0% do footage baixado).
   ============================================================ */

const isVideo = (s: string) => /\.(mp4|webm|mov|m4v)$/i.test(s);

/* ---- fundo: grid em perspectiva com distorção barrel ---- */
const PerspectiveGrid: React.FC<{ color: string; frame: number }> = ({ color, frame }) => {
  const { width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const breathe = interpolate(Math.sin(frame / 40), [-1, 1], [0.97, 1.03]);
  const halfX = width * 0.62 * breathe;
  const halfY = height * 0.62 * breathe;
  const k = 0.22; // curvatura barrel (quanto maior, mais bojudo nas quinas)
  const N = 11; // linhas por direção
  const S = 16; // amostras por linha

  const distort = (u: number, v: number): [number, number] => {
    const factor = 1 + k * (u * u + v * v);
    return [cx + u * factor * halfX, cy + v * factor * halfY];
  };
  const line = (fixed: number, horizontal: boolean) => {
    let d = "";
    for (let i = 0; i <= S; i++) {
      const t = (i / S) * 2 - 1;
      const [x, y] = horizontal ? distort(t, fixed) : distort(fixed, t);
      d += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1) + " ";
    }
    return d;
  };
  const lines: string[] = [];
  for (let j = 0; j <= N; j++) {
    const p = (j / N) * 2 - 1;
    lines.push(line(p, true));
    lines.push(line(p, false));
  }

  return (
    <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
      {lines.map((d, i) => (
        <path key={i} d={d} fill="none" stroke={color} strokeWidth={1.6} opacity={0.72} />
      ))}
      {/* glow central sutil */}
      <defs>
        <radialGradient id="fgm-glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor={color} stopOpacity={0.10} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect width={width} height={height} fill="url(#fgm-glow)" />
    </svg>
  );
};

/* ---- um sub-clipe (imagem ou vídeo mudo) com pop de corte + drift ---- */
const Clip: React.FC<{ src: string; per: number }> = ({ src, per }) => {
  const f = useCurrentFrame();
  const drift = interpolate(f, [0, per], [1.05, 1.12], { extrapolateRight: "clamp" });
  const pop = interpolate(f, [0, 3], [1.09, 1], { extrapolateRight: "clamp" });
  const scale = drift * pop;
  const common: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: `scale(${scale})`,
  };
  return isVideo(src) ? (
    <OffthreadVideo src={staticFile(src)} muted volume={0} style={common} />
  ) : (
    <Img src={staticFile(src)} style={common} />
  );
};

export const FramedGridMontage: React.FC<{
  clips?: string[];
  clipDuration?: number; // frames por sub-clipe (30–60 ≈ 1–2s)
  border?: string;
  gridColor?: string;
  accent?: string;
  sparks?: boolean;
  caption?: string;
}> = ({
  clips = [
    "jobs/motos2/clips/moto0.jpg",
    "jobs/motos2/clips/moto11.jpg",
    "jobs/motos2/clips/moto12.jpg",
    "jobs/motos2/clips/moto13.jpg",
    "jobs/motos2/clips/moto10.jpg",
  ],
  clipDuration = 45,
  border = "rgba(150,180,255,0.9)",
  gridColor = "#3a4a72",
  accent = "#f59e0b",
  sparks = true,
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const per = clipDuration;
  const total = clips.length * per;
  const idx = Math.min(clips.length - 1, Math.floor((frame % total) / per));

  const FW = Math.round(width * 0.665);
  const FH = Math.round(height * 0.62);
  const intro = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 46%, #0c1120 0%, #05060a 100%)" }}>
      <PerspectiveGrid color={gridColor} frame={frame} />

      {/* moldura fixa com os sub-clipes trocando em corte seco */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            position: "relative",
            width: FW,
            height: FH,
            borderRadius: 16,
            overflow: "hidden",
            border: `3px solid ${border}`,
            boxShadow: `0 32px 90px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.06), 0 0 46px ${border}`,
            transform: `scale(${interpolate(intro, [0, 1], [0.94, 1])})`,
            opacity: intro,
            background: "#000",
          }}
        >
          {clips.map((c, i) => (
            <Sequence key={i} from={i * per} durationInFrames={per} layout="none">
              <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
                <Clip src={c} per={per} />
              </div>
            </Sequence>
          ))}
          {/* leve gradiente de leitura na moldura */}
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(0,0,0,0.12) 0%, transparent 22%, transparent 78%, rgba(0,0,0,0.28) 100%)" }} />
        </div>

        {/* pontinhos de progresso da montagem */}
        <div style={{ display: "flex", gap: 9, marginTop: 22 }}>
          {clips.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === idx ? 26 : 9,
                height: 9,
                borderRadius: 6,
                background: i === idx ? accent : "rgba(255,255,255,0.28)",
                transition: "all 0.2s",
              }}
            />
          ))}
        </div>
        {caption ? (
          <div style={{ marginTop: 16, color: "#fff", fontFamily: "'Archivo Black','Impact',sans-serif", fontSize: 34, letterSpacing: 0.4, textShadow: "0 3px 18px rgba(0,0,0,0.8)" }}>
            {caption}
          </div>
        ) : null}
      </AbsoluteFill>

      {/* fagulhas subindo (eco do fogo da ref) */}
      {sparks && (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          {Array.from({ length: 26 }).map((_, i) => {
            const seed = (i * 97) % 100;
            const x = (seed / 100) * width;
            const speed = 0.5 + ((i * 37) % 60) / 60;
            const y = height - ((frame * speed * 6 + seed * 11) % (height + 60));
            const size = 2 + ((i * 13) % 3);
            const op = interpolate(y, [0, height * 0.3, height], [0, 0.9, 0], { extrapolateLeft: "clamp" });
            return (
              <div key={i} style={{ position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%", background: accent, opacity: op * 0.8, boxShadow: `0 0 6px ${accent}` }} />
            );
          })}
        </AbsoluteFill>
      )}

      {/* grão / scanline sutil */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.028) 0 2px, transparent 2px 4px)", opacity: 0.5, mixBlendMode: "overlay" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 92% 92% at 50% 50%, transparent 62%, rgba(0,0,0,0.4) 100%)" }} />
    </AbsoluteFill>
  );
};
