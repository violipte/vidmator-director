import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// SPLIT SCREEN COMPARISON — split-screen: metade esquerda uma imagem, metade direita outra,
// com divisor central luminoso. Container do acervo VidMator.
// Niche-agnostic: leftImage/rightImage/accent via props.
const BG = "#0a0b0f";

export const SplitScreenComparison: React.FC<{
  leftImage?: string;
  rightImage?: string;
  accent?: string;
}> = ({
  leftImage = "test/people/pessoa_0.png",
  rightImage = "test/clips/scene_10.jpg",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sl = spring({ frame, fps, config: { damping: 17, stiffness: 80 }, durationInFrames: 24 });
  const sr = spring({ frame: frame - 5, fps, config: { damping: 17, stiffness: 80 }, durationInFrames: 24 });
  const lx = interpolate(sl, [0, 1], [-100, 0]);
  const rx = interpolate(sr, [0, 1], [100, 0]);
  const kb = interpolate(frame, [0, 150], [1.05, 1.14]);

  const divGlow = 0.5 + 0.5 * Math.sin(frame / 12);
  const dividerReveal = interpolate(spring({ frame: frame - 10, fps, config: { damping: 20 }, durationInFrames: 22 }), [0, 1], [0, 100]);

  return (
    <AbsoluteFill style={{ background: BG, overflow: "hidden" }}>
      {/* metade esquerda */}
      <div style={{ position: "absolute", left: 0, top: 0, width: "50%", height: "100%", overflow: "hidden", transform: `translateX(${lx}%)` }}>
        <Img src={staticFile(leftImage)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", transform: `scale(${kb})` }} />
        <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(0,0,0,0.25) 0%, transparent 30%, rgba(0,0,0,0.3) 100%)" }} />
      </div>

      {/* metade direita */}
      <div style={{ position: "absolute", right: 0, top: 0, width: "50%", height: "100%", overflow: "hidden", transform: `translateX(${rx}%)` }}>
        <Img src={staticFile(rightImage)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", transform: `scale(${kb})` }} />
        <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(0,0,0,0.3) 0%, transparent 70%, rgba(0,0,0,0.25) 100%)" }} />
      </div>

      {/* divisor central */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: `${(100 - dividerReveal) / 2}%`,
          height: `${dividerReveal}%`,
          width: 6,
          transform: "translateX(-3px)",
          background: "#fff",
          boxShadow: `0 0 ${18 + divGlow * 20}px ${accent}, 0 0 6px #fff`,
        }}
      />
      {/* selo VS no centro */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
        <div
          style={{
            width: 118,
            height: 118,
            borderRadius: "50%",
            background: "#0a0b0f",
            border: `4px solid ${accent}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "'Archivo Black', 'Impact', sans-serif",
            fontSize: 46,
            color: "#fff",
            boxShadow: `0 0 ${24 + divGlow * 22}px ${accent}, inset 0 0 22px rgba(0,0,0,0.6)`,
            transform: `scale(${interpolate(spring({ frame: frame - 18, fps, config: { damping: 10, stiffness: 140 }, durationInFrames: 18 }), [0, 1], [0, 1])})`,
          }}
        >
          VS
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
