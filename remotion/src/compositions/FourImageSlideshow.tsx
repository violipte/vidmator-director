import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// FOUR IMAGE SLIDESHOW — 4 fotos emolduradas passam em sequência (slide/fade)
// sobre um fundo GRID sutil. Container do acervo VidMator.
// Niche-agnostic: images[4]/accent via props.
const BG = "#0a0b0f";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const FourImageSlideshow: React.FC<{
  images?: string[];
  accent?: string;
}> = ({
  images = ["test/clips/scene_10.jpg", "test/clips/scene_100.jpg", "test/clips/scene_101.jpg", "test/clips/scene_102.jpg"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const imgs = [0, 1, 2, 3].map((i) => images[i] ?? images[images.length - 1] ?? images[0]);

  const per = durationInFrames / imgs.length; // frames por slide

  return (
    <AbsoluteFill style={{ background: BG }}>
      {/* fundo grid */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        }}
      />
      <AbsoluteFill style={{ background: `radial-gradient(90% 90% at 50% 45%, ${accent}12 0%, transparent 60%)` }} />

      {imgs.map((src, i) => {
        const start = i * per;
        const local = frame - start;
        // entra: slide da direita + fade; sai: fade + leve slide pra esquerda
        const inS = spring({ frame: local, fps, config: { damping: 16, stiffness: 80 }, durationInFrames: 20 });
        const outT = interpolate(local, [per - 14, per], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const active = local >= -2 && local <= per + 2;
        if (!active) return null;
        const x = interpolate(inS, [0, 1], [220, 0]) - outT * 180;
        const op = Math.min(interpolate(local, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), 1 - outT);
        const kb = interpolate(local, [0, per], [1.02, 1.12]);

        return (
          <AbsoluteFill key={i} style={{ alignItems: "center", justifyContent: "center", opacity: op }}>
            <div
              style={{
                width: "64%",
                height: "72%",
                borderRadius: 18,
                overflow: "hidden",
                border: "4px solid rgba(255,255,255,0.92)",
                boxShadow: `0 30px 80px rgba(0,0,0,0.75), 0 0 0 7px ${accent}22`,
                transform: `translateX(${x}px)`,
              }}
            >
              <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }} />
            </div>
            {/* indicador de posição */}
            <div style={{ position: "absolute", bottom: 56, display: "flex", gap: 14 }}>
              {imgs.map((_, k) => (
                <div
                  key={k}
                  style={{
                    width: k === i ? 40 : 14,
                    height: 14,
                    borderRadius: 7,
                    background: k === i ? accent : "rgba(255,255,255,0.25)",
                    boxShadow: k === i ? `0 0 14px ${accent}` : "none",
                    transition: "none",
                    fontFamily: SANS,
                  }}
                />
              ))}
            </div>
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
