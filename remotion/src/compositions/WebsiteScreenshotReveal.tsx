import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// WEBSITE SCREENSHOT REVEAL — túnel 3D escuro (perspectiva com linhas convergindo); ao fundo
// distante um "print de site" emoldurado que se APROXIMA/revela; a url pequena embaixo.
// Container do acervo VidMator (ref.: VidRush "reveal de site/tool"). Niche-agnostic via props.
const MONO = "'American Typewriter','Courier New',monospace";
const SANS = "'Inter','Segoe UI',sans-serif";

export const WebsiteScreenshotReveal: React.FC<{
  url?: string;
  screenshot?: string;
  accent?: string;
}> = ({
  url = "https://vidrush.ai",
  screenshot = "test/clips/scene_100.jpg",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // aproximação do print: começa pequeno/distante, cresce até enquadrar
  const approach = spring({ frame, fps, config: { damping: 22, stiffness: 46 }, durationInFrames: 60 });
  const scale = interpolate(approach, [0, 1], [0.12, 1]);
  const shotOp = interpolate(frame, [4, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const urlOp = interpolate(frame, [40, 58], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cx = width / 2;
  const cy = height / 2 - 30;
  const drift = Math.sin(frame / 50) * 8;

  // linhas de perspectiva convergindo p/ o ponto de fuga
  const rays = Array.from({ length: 24 });

  return (
    <AbsoluteFill style={{ background: "#05060a", overflow: "hidden", fontFamily: SANS }}>
      {/* fundo túnel: gradiente radial escuro convergindo */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(60% 60% at 50% 46%, ${accent}12 0%, #0a0d16 34%, #05060a 78%)`,
        }}
      />

      {/* linhas de perspectiva (SVG) */}
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <radialGradient id="wsFog" cx="50%" cy="46%" r="55%">
            <stop offset="0%" stopColor={accent} stopOpacity="0.28" />
            <stop offset="100%" stopColor={accent} stopOpacity="0" />
          </radialGradient>
        </defs>
        {rays.map((_, i) => {
          const ang = (i / rays.length) * Math.PI * 2;
          const x2 = cx + Math.cos(ang) * width;
          const y2 = cy + Math.sin(ang) * width;
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={x2}
              y2={y2}
              stroke={accent}
              strokeWidth={1}
              opacity={0.10 + 0.05 * Math.abs(Math.sin(i + frame / 30))}
            />
          );
        })}
        {/* anéis concêntricos que "vêm em direção" à câmera */}
        {[0, 1, 2, 3].map((k) => {
          const phase = ((frame / 90 + k / 4) % 1);
          const r = 40 + phase * 900;
          return <circle key={`r${k}`} cx={cx} cy={cy} r={r} fill="none" stroke={accent} strokeWidth={1.5} opacity={(1 - phase) * 0.22} />;
        })}
        <circle cx={cx} cy={cy} r={280} fill="url(#wsFog)" />
      </svg>

      {/* print de site emoldurado, aproximando */}
      <div
        style={{
          position: "absolute",
          left: cx,
          top: cy + drift,
          transform: `translate(-50%,-50%) scale(${scale})`,
          opacity: shotOp,
          width: 1180,
          borderRadius: 14,
          overflow: "hidden",
          background: "#14161c",
          border: `2px solid ${accent}`,
          boxShadow: `0 30px 90px rgba(0,0,0,0.75), 0 0 60px ${accent}44`,
        }}
      >
        {/* barra de navegador */}
        <div
          style={{
            height: 46,
            background: "#1b1e26",
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "0 18px",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#ff5f56" }} />
          <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#ffbd2e" }} />
          <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#27c93f" }} />
          <div
            style={{
              marginLeft: 18,
              flex: 1,
              height: 26,
              borderRadius: 13,
              background: "#0d0f14",
              color: "#9aa4b2",
              fontFamily: MONO,
              fontSize: 18,
              display: "flex",
              alignItems: "center",
              padding: "0 16px",
            }}
          >
            {url}
          </div>
        </div>
        <Img src={staticFile(screenshot)} style={{ width: "100%", height: 620, objectFit: "cover", display: "block" }} />
      </div>

      {/* url grande embaixo */}
      <div
        style={{
          position: "absolute",
          bottom: 70,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: urlOp,
          fontFamily: MONO,
          fontSize: 34,
          letterSpacing: 2,
          color: accent,
          textShadow: `0 0 22px ${accent}88`,
        }}
      >
        {url}
      </div>

      {/* vinheta */}
      <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at center, transparent 52%, rgba(0,0,0,0.72) 100%)" }} />
    </AbsoluteFill>
  );
};
