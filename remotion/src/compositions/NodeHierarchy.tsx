import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// NODE HIERARCHY — 1 nó no topo + 3 nós embaixo, ligados por LINHAS (SVG) que se desenham.
// Container do acervo VidMator (ref.: VidRush "org / relation map"). Niche-agnostic via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";
const W = 1920;
const H = 1080;

export const NodeHierarchy: React.FC<{
  topNode?: string;
  bottomNodes?: string[];
  accent?: string;
}> = ({
  topNode = "jobs/motos2/clips/moto0.jpg",
  bottomNodes = ["test/people/pessoa_0.png", "test/people/pessoa_1.png", "test/people/pessoa_4.png"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const nodes = bottomNodes.slice(0, 3);
  const topR = 130;
  const botR = 100;
  const topPos = { x: W / 2, y: 240 };
  const botY = 800;
  const botXs = [W / 2 - 560, W / 2, W / 2 + 560];

  const topIn = spring({ frame, fps, config: { damping: 16 }, durationInFrames: 20 });
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = 0.5 + 0.5 * Math.sin(frame / 16);

  const NodeCircle = ({ src, cx, cy, r, ap, sc }: { src: string; cx: number; cy: number; r: number; ap: number; sc: number }) => (
    <div
      style={{
        position: "absolute",
        left: cx - r,
        top: cy - r,
        width: r * 2,
        height: r * 2,
        borderRadius: "50%",
        overflow: "hidden",
        border: `4px solid ${accent}`,
        boxShadow: `0 0 ${18 + glow * 16}px ${accent}66, 0 16px 40px rgba(0,0,0,0.6)`,
        opacity: ap,
        transform: `scale(${sc})`,
        background: "#14161c",
      }}
    >
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }} />
    </div>
  );

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", opacity: outOp, overflow: "hidden", fontFamily: SANS }}>
      {/* grade sutil */}
      <AbsoluteFill
        style={{
          background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
          maskImage: "radial-gradient(ellipse 80% 80% at 50% 50%, black 45%, transparent 95%)",
        }}
      />

      {/* linhas conectoras (desenham escalonado) */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {nodes.map((_, i) => {
          const x2 = botXs[i];
          const dx = x2 - topPos.x;
          const dy = botY - topPos.y;
          const len = Math.sqrt(dx * dx + dy * dy);
          const draw = interpolate(frame - (14 + i * 6), [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <line
              key={i}
              x1={topPos.x}
              y1={topPos.y + topR}
              x2={x2}
              y2={botY - botR}
              stroke={accent}
              strokeWidth={4}
              strokeLinecap="round"
              strokeDasharray={len}
              strokeDashoffset={len * (1 - draw)}
              opacity={0.85}
              style={{ filter: `drop-shadow(0 0 6px ${accent}88)` }}
            />
          );
        })}
      </svg>

      {/* nó do topo */}
      <NodeCircle src={topNode} cx={topPos.x} cy={topPos.y} r={topR} ap={topIn} sc={0.85 + 0.15 * topIn} />

      {/* nós embaixo, entrada escalonada */}
      {nodes.map((src, i) => {
        const ni = spring({ frame: frame - (24 + i * 8), fps, config: { damping: 14, stiffness: 110 }, durationInFrames: 18 });
        return <NodeCircle key={i} src={src} cx={botXs[i]} cy={botY} r={botR} ap={ni} sc={0.7 + 0.3 * ni} />;
      })}
    </AbsoluteFill>
  );
};
