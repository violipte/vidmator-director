import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// DUAL IMAGE ON GRID — fundo PAPEL QUADRICULADO branco; 2 fotos (leve rotação) lado a lado
// + labels em tag amarela (leftLabel/rightLabel). Container do acervo VidMator.
// Niche-agnostic: leftImage/rightImage/leftLabel/rightLabel/accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

export const DualImageOnGrid: React.FC<{
  leftImage?: string;
  rightImage?: string;
  leftLabel?: string;
  rightLabel?: string;
  accent?: string;
}> = ({
  leftImage = "test/clips/scene_10.jpg",
  rightImage = "jobs/motos2/clips/moto0.jpg",
  leftLabel = "1815",
  rightLabel = "1914",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sl = spring({ frame: frame - 4, fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 24 });
  const sr = spring({ frame: frame - 12, fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 24 });
  const tagL = spring({ frame: frame - 20, fps, config: { damping: 11, stiffness: 130 }, durationInFrames: 16 });
  const tagR = spring({ frame: frame - 26, fps, config: { damping: 11, stiffness: 130 }, durationInFrames: 16 });

  const Card: React.FC<{ src: string; label: string; s: number; tag: number; rot: number; y: number }> = ({ src, label, s, tag, rot, y }) => (
    <div style={{ position: "relative", opacity: s, transform: `translateY(${y}px) rotate(${rot}deg) scale(${interpolate(s, [0, 1], [0.8, 1])})` }}>
      {/* moldura tipo polaroid sobre o papel */}
      <div style={{ background: "#fff", padding: 16, paddingBottom: 20, borderRadius: 4, boxShadow: "0 22px 50px rgba(20,25,40,0.28)", border: "1px solid rgba(0,0,0,0.08)" }}>
        <div style={{ width: 620, height: 500, overflow: "hidden", borderRadius: 2 }}>
          <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </div>
      {/* tag amarela */}
      <div
        style={{
          position: "absolute",
          bottom: -34,
          left: "50%",
          transform: `translateX(-50%) rotate(${-rot}deg) scale(${tag})`,
          background: accent,
          color: "#1a1205",
          fontFamily: DISPLAY,
          fontSize: 46,
          padding: "10px 34px",
          borderRadius: 10,
          letterSpacing: 1,
          boxShadow: "0 10px 26px rgba(0,0,0,0.28)",
          border: "3px solid #fff",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </div>
    </div>
  );

  return (
    <AbsoluteFill
      style={{
        background: "#f7f6f1",
        backgroundImage:
          "repeating-linear-gradient(0deg, rgba(90,130,180,0.16) 0 1px, transparent 1px 46px), repeating-linear-gradient(90deg, rgba(90,130,180,0.16) 0 1px, transparent 1px 46px)",
        alignItems: "center",
        justifyContent: "center",
        gap: 90,
      }}
    >
      <Card src={leftImage} label={leftLabel} s={sl} tag={tagL} rot={-4} y={interpolate(sl, [0, 1], [40, 0])} />
      <Card src={rightImage} label={rightLabel} s={sr} tag={tagR} rot={3.5} y={interpolate(sr, [0, 1], [40, 0])} />
    </AbsoluteFill>
  );
};
