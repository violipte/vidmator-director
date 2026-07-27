import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// FOUR IMAGE CAPTION GRID — grid 2x2 de fotos emolduradas, cada uma com legenda
// (se showText). Entrada escalonada em pop. Container do acervo VidMator.
// Niche-agnostic: images[4]/captions[4]/showText/accent via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";
const BG = "#0a0b0f";

export const FourImageCaptionGrid: React.FC<{
  images?: string[];
  captions?: string[];
  showText?: boolean;
  accent?: string;
}> = ({
  images = ["test/clips/scene_10.jpg", "test/clips/scene_100.jpg", "test/clips/scene_101.jpg", "test/clips/scene_102.jpg"],
  captions = ["First", "Second", "Third", "Fourth"],
  showText = true,
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cells = [0, 1, 2, 3];

  return (
    <AbsoluteFill style={{ background: BG }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        }}
      />
      <AbsoluteFill
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gridTemplateRows: "1fr 1fr",
          gap: 40,
          padding: 70,
        }}
      >
        {cells.map((i) => {
          const s = spring({ frame: frame - i * 6, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 20 });
          const src = images[i] ?? images[images.length - 1] ?? images[0];
          const cap = captions[i] ?? "";
          const kb = interpolate(frame, [0, 150], [1.02, 1.1]);
          return (
            <div
              key={i}
              style={{
                position: "relative",
                borderRadius: 16,
                overflow: "hidden",
                border: "4px solid rgba(255,255,255,0.9)",
                boxShadow: `0 22px 60px rgba(0,0,0,0.7), 0 0 0 6px ${accent}22`,
                opacity: s,
                transform: `scale(${interpolate(s, [0, 1], [0.82, 1])})`,
              }}
            >
              <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }} />
              {showText && cap ? (
                <>
                  <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, transparent 55%, rgba(0,0,0,0.82) 100%)" }} />
                  <div
                    style={{
                      position: "absolute",
                      left: 24,
                      bottom: 22,
                      display: "flex",
                      alignItems: "center",
                      gap: 14,
                      opacity: interpolate(frame - i * 6, [10, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                    }}
                  >
                    <div style={{ width: 8, height: 34, background: accent, borderRadius: 4, boxShadow: `0 0 14px ${accent}` }} />
                    <span style={{ fontFamily: SANS, fontWeight: 700, fontSize: 34, color: "#fff", letterSpacing: 0.5, textShadow: "0 2px 12px rgba(0,0,0,0.8)" }}>{cap}</span>
                  </div>
                </>
              ) : null}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
