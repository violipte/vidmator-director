import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// FIVE TEXT LISTICLE — 5 mini-fotos emolduradas numa fila + label embaixo de cada
// (FIRST..FIFTH), entrando escalonado (pop de baixo). Container do acervo VidMator.
// Niche-agnostic: items[{image,text}]/accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";
const BG = "#0a0b0f";

type Item = { image: string; text: string };

export const FiveTextListicle: React.FC<{
  items?: Item[];
  accent?: string;
}> = ({
  items = [
    { image: "test/clips/scene_10.jpg", text: "FIRST TEXT" },
    { image: "test/clips/scene_100.jpg", text: "SECOND TEXT" },
    { image: "test/clips/scene_101.jpg", text: "THIRD TEXT" },
    { image: "test/clips/scene_102.jpg", text: "FOURTH TEXT" },
    { image: "test/clips/scene_10.jpg", text: "FIFTH TEXT" },
  ],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const list = items.length ? items : [{ image: "test/clips/scene_10.jpg", text: "FIRST" }];

  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 100% at 50% 30%, #14161c 0%, ${BG} 72%)` }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 64px)",
        }}
      />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 34, padding: "0 60px" }}>
        {list.map((it, i) => {
          const s = spring({ frame: frame - i * 7, fps, config: { damping: 13, stiffness: 110 }, durationInFrames: 20 });
          const y = interpolate(s, [0, 1], [70, 0]);
          const labelOp = interpolate(frame - i * 7, [12, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: s, transform: `translateY(${y}px)`, width: `${100 / list.length}%` }}>
              {/* número */}
              <div style={{ fontFamily: DISPLAY, fontSize: 40, color: accent, marginBottom: 12, textShadow: `0 0 18px ${accent}88` }}>
                {String(i + 1).padStart(2, "0")}
              </div>
              {/* mini-foto emoldurada */}
              <div
                style={{
                  width: "100%",
                  aspectRatio: "3 / 4",
                  borderRadius: 14,
                  overflow: "hidden",
                  border: "3px solid rgba(255,255,255,0.9)",
                  boxShadow: `0 20px 50px rgba(0,0,0,0.7), 0 0 0 5px ${accent}22`,
                }}
              >
                <Img src={staticFile(it.image)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
              {/* label embaixo */}
              <div
                style={{
                  marginTop: 18,
                  fontFamily: SANS,
                  fontWeight: 800,
                  fontSize: 26,
                  color: "#fff",
                  textAlign: "center",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  opacity: labelOp,
                  background: "rgba(255,255,255,0.06)",
                  border: `1px solid ${accent}55`,
                  borderRadius: 8,
                  padding: "8px 12px",
                  width: "100%",
                  boxSizing: "border-box",
                }}
              >
                {it.text}
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
