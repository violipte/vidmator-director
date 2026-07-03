import { AbsoluteFill, OffthreadVideo, Loop, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Footage de ARQUIVO (archive.org, SD/4:3/granulado) com 2 modos:
//  - "fundir": upscale cover 16:9, leve grade vintage -> passa como mais footage
//  - "enquadrar": janela 4:3 com moldura + fundo borrado + grão forte + tag ARCHIVE (registro histórico)

const W = 1920, H = 1080;

const Grain: React.FC<{ op?: number; seed?: number }> = ({ op = 0.12, seed = 4 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: op, pointerEvents: "none" }}>
      <svg width={W} height={H}>
        <filter id={`gr${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={seed + (f % 4)} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width={W} height={H} filter={`url(#gr${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const ArchiveClip: React.FC<{ rel: string; modo?: "fundir" | "enquadrar"; era?: string; durFrames?: number }> = ({
  rel, modo = "fundir", era = "ARCHIVE", durFrames,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const total = durFrames || durationInFrames;
  const src = staticFile(rel);
  const flicker = 1 - 0.05 * Math.abs(Math.sin(frame * 1.7)); // tremor de projeção
  const video = (style: React.CSSProperties) => (
    <Loop durationInFrames={Math.max(1, Math.floor(total))}>
      <OffthreadVideo src={src} muted style={style} />
    </Loop>
  );

  if (modo === "fundir") {
    return (
      <AbsoluteFill style={{ backgroundColor: "black" }}>
        {video({ width: W, height: H, objectFit: "cover", filter: "sepia(0.22) contrast(1.04) saturate(0.85) brightness(1.02)" })}
        <AbsoluteFill style={{ mixBlendMode: "soft-light", opacity: 0.3, background: "linear-gradient(160deg,#3a2a12,transparent 60%)", pointerEvents: "none" }} />
        <Grain op={0.1} seed={3} />
      </AbsoluteFill>
    );
  }

  // enquadrar: fundo borrado + janela 4:3 com moldura + tag
  return (
    <AbsoluteFill style={{ backgroundColor: "#05070b" }}>
      {/* fundo: mesmo vídeo borrado/escurecido */}
      {video({ width: W, height: H, objectFit: "cover", filter: "blur(28px) brightness(0.4) saturate(0.7)" })}
      <AbsoluteFill style={{ background: "rgba(3,5,10,0.5)", pointerEvents: "none" }} />
      {/* janela do arquivo (4:3), opacidade com flicker */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ position: "relative", height: 880, width: 880 * 4 / 3, opacity: flicker,
          border: "3px solid rgba(235,225,200,0.85)", boxShadow: "0 18px 60px rgba(0,0,0,0.75)", overflow: "hidden" }}>
          <OffthreadVideo src={src} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(0.3) contrast(1.08) saturate(0.7)" }} />
          {/* vinheta dentro da janela */}
          <AbsoluteFill style={{ boxShadow: "inset 0 0 120px 30px rgba(0,0,0,0.7)", pointerEvents: "none" }} />
        </div>
      </AbsoluteFill>
      <Grain op={0.18} seed={6} />
      {/* tag de arquivo */}
      <div style={{ position: "absolute", top: 60, left: 90, display: "flex", alignItems: "center", gap: 12,
        fontFamily: "'Consolas',monospace", fontSize: 28, color: "#e9e2cf", letterSpacing: 2, textShadow: "0 2px 8px #000" }}>
        <span style={{ width: 14, height: 14, borderRadius: "50%", background: "#e0452e", opacity: 0.5 + 0.5 * Math.abs(Math.sin(frame / 6)) }} />
        REC · {era}
      </div>
    </AbsoluteFill>
  );
};

// ---- Composição DEMO: mostra os 2 modos ----
export const ArchiveDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const half = 5 * fps;
  const isFirst = frame < half;
  return (
    <AbsoluteFill>
      {isFirst
        ? <ArchiveClip rel="test/archive/space_apollo.mp4" modo="fundir" era="NASA 1969" durFrames={half} />
        : <ArchiveClip rel="test/archive/vint_palms.mp4" modo="enquadrar" era="1935" durFrames={half} />}
      {/* legenda do modo (só pro demo) */}
      <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, textAlign: "center",
        fontFamily: "'Segoe UI',system-ui,sans-serif", fontSize: 30, fontWeight: 700, color: "#fff", textShadow: "0 2px 10px #000" }}>
        {isFirst ? "modo FUNDIR — Apollo (espaço) preenche 16:9 + grade vintage" : "modo ENQUADRAR — moldura de arquivo + tag + grão"}
      </div>
    </AbsoluteFill>
  );
};
