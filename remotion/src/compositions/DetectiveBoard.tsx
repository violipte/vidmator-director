import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// DETECTIVE BOARD — quadro de investigação (true crime): 2 fotos "pregadas" com pin + títulos,
// ligadas por um BARBANTE VERMELHO (SVG) que se desenha. Fundo cortiça/escuro, vibe dramática.
// Container do acervo VidMator. Niche-agnostic via props com defaults.
const TYPE = "'American Typewriter', 'Courier New', monospace";
const RED = "#c62828";
const W = 1920;
const H = 1080;

export const DetectiveBoard: React.FC<{
  leftImage?: string;
  leftTitle?: string;
  rightImage?: string;
  rightTitle?: string;
  accent?: string;
}> = ({
  leftImage = "test/people/pessoa_1.png",
  leftTitle = "Historical Figure",
  rightImage = "test/people/pessoa_4.png",
  rightTitle = "Theodore Simon",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // pontos das fotos (centro do card)
  const leftC = { x: 520, y: 520 };
  const rightC = { x: 1400, y: 520 };
  const dx = rightC.x - leftC.x;
  const dy = rightC.y - leftC.y;
  const strLen = Math.sqrt(dx * dx + dy * dy);
  const draw = interpolate(frame - 34, [0, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const Photo = ({
    src,
    title,
    cx,
    cy,
    rot,
    delay,
  }: {
    src: string;
    title: string;
    cx: number;
    cy: number;
    rot: number;
    delay: number;
  }) => {
    const e = spring({ frame: frame - delay, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 18 });
    const op = interpolate(frame - delay, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const cardW = 340;
    const cardH = 400;
    return (
      <div
        style={{
          position: "absolute",
          left: cx - cardW / 2,
          top: cy - cardH / 2,
          width: cardW,
          height: cardH,
          background: "#f4efe2",
          padding: "18px 18px 14px",
          boxShadow: "0 22px 46px rgba(0,0,0,0.7)",
          transform: `rotate(${rot}deg) scale(${interpolate(e, [0, 1], [0.7, 1])})`,
          opacity: op,
          border: "1px solid rgba(0,0,0,0.15)",
        }}
      >
        {/* pin */}
        <div
          style={{
            position: "absolute",
            top: -14,
            left: "50%",
            width: 26,
            height: 26,
            marginLeft: -13,
            borderRadius: "50%",
            background: `radial-gradient(circle at 35% 30%, #ff6b6b, ${RED})`,
            boxShadow: "0 4px 8px rgba(0,0,0,0.6)",
            border: "2px solid rgba(0,0,0,0.2)",
          }}
        />
        <div style={{ width: "100%", height: 288, overflow: "hidden", background: "#222" }}>
          <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top center", filter: "grayscale(0.35) contrast(1.05)" }} />
        </div>
        <div
          style={{
            marginTop: 12,
            textAlign: "center",
            fontFamily: TYPE,
            fontSize: 26,
            fontWeight: 700,
            letterSpacing: 1,
            color: "#1a1a1a",
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
      </div>
    );
  };

  return (
    <AbsoluteFill style={{ opacity: outOp, overflow: "hidden", fontFamily: TYPE }}>
      {/* fundo cortiça escura */}
      <AbsoluteFill
        style={{
          background: "radial-gradient(120% 120% at 50% 40%, #4a3b28 0%, #2e2418 55%, #1a140d 100%)",
        }}
      />
      {/* textura granulada da cortiça */}
      <AbsoluteFill
        style={{
          background: "repeating-radial-gradient(circle at 20% 30%, rgba(0,0,0,0.12) 0 2px, transparent 2px 5px), repeating-radial-gradient(circle at 70% 70%, rgba(255,255,255,0.05) 0 1px, transparent 1px 4px)",
          opacity: 0.6,
          mixBlendMode: "overlay",
        }}
      />
      {/* vinheta dramática */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 90% at 50% 50%, transparent 40%, rgba(0,0,0,0.7) 100%)" }} />

      {/* barbante vermelho ligando as fotos (desenha) */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <line
          x1={leftC.x}
          y1={leftC.y}
          x2={rightC.x}
          y2={rightC.y}
          stroke={RED}
          strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={strLen}
          strokeDashoffset={strLen * (1 - draw)}
          style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.6))" }}
        />
      </svg>

      {/* header de dossiê */}
      <div
        style={{
          position: "absolute",
          top: 70,
          left: 0,
          right: 0,
          textAlign: "center",
          color: accent,
          fontSize: 34,
          fontWeight: 700,
          letterSpacing: 8,
          textTransform: "uppercase",
          opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" }),
          textShadow: "0 2px 10px rgba(0,0,0,0.8)",
        }}
      >
        Case File
      </div>

      <Photo src={leftImage} title={leftTitle} cx={leftC.x} cy={leftC.y} rot={-5} delay={6} />
      <Photo src={rightImage} title={rightTitle} cx={rightC.x} cy={rightC.y} rot={4} delay={16} />
    </AbsoluteFill>
  );
};
