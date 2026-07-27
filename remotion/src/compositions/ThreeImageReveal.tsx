import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// THREE IMAGE REVEAL — começa na imagem do MEIO em tela cheia e dá ZOOM-OUT
// revelando as 3 fotos emolduradas em fila. Container do acervo VidMator.
// Niche-agnostic: images[3]/accent via props.
const BG = "#0a0b0f";

export const ThreeImageReveal: React.FC<{
  images?: string[];
  accent?: string;
}> = ({
  images = ["test/clips/scene_10.jpg", "test/clips/scene_100.jpg", "test/clips/scene_101.jpg"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const imgs = [0, 1, 2].map((i) => images[i] ?? images[images.length - 1] ?? images[0]);

  // t=0 -> imagem do meio ocupa a tela; t=1 -> encolhe pro slot central da fila.
  const reveal = spring({ frame: frame - 12, fps, config: { damping: 18, stiffness: 70 }, durationInFrames: 34 });

  // moldura central: de "tela cheia" (100% da tela) até o slot (~30% de largura).
  const centerW = interpolate(reveal, [0, 1], [100, 30]);
  const centerH = interpolate(reveal, [0, 1], [100, 60]);
  const centerRadius = interpolate(reveal, [0, 1], [0, 16]);
  const centerBorder = interpolate(reveal, [0, 1], [0, 4]);

  // laterais aparecem no fim do zoom-out
  const sideOp = interpolate(reveal, [0.55, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sideL = spring({ frame: frame - 28, fps, config: { damping: 15 }, durationInFrames: 22 });
  const sideR = spring({ frame: frame - 33, fps, config: { damping: 15 }, durationInFrames: 22 });

  const sideFrame = (op: number, sx: number, rot: number): React.CSSProperties => ({
    width: "30%",
    height: "60%",
    borderRadius: 16,
    overflow: "hidden",
    border: "4px solid rgba(255,255,255,0.92)",
    boxShadow: `0 24px 70px rgba(0,0,0,0.7), 0 0 0 6px ${accent}22`,
    opacity: op,
    transform: `translateX(${sx}px) rotate(${rot}deg)`,
  });

  return (
    <AbsoluteFill style={{ background: BG, alignItems: "center", justifyContent: "center", gap: 44 }}>
      <div style={sideFrame(sideOp, interpolate(sideL, [0, 1], [-120, 0]), -3)}>
        <Img src={staticFile(imgs[0])} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>

      <div
        style={{
          width: `${centerW}%`,
          height: `${centerH}%`,
          borderRadius: centerRadius,
          overflow: "hidden",
          border: `${centerBorder}px solid rgba(255,255,255,0.92)`,
          boxShadow: `0 24px 80px rgba(0,0,0,0.75), 0 0 0 ${centerBorder * 1.5}px ${accent}22`,
          zIndex: 2,
        }}
      >
        <Img src={staticFile(imgs[1])} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>

      <div style={sideFrame(sideOp, interpolate(sideR, [0, 1], [120, 0]), 3)}>
        <Img src={staticFile(imgs[2])} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
    </AbsoluteFill>
  );
};
