import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// DATE / LOCATION OVERLAY — lower-third: barra accent vertical (cresce) + pill escura
// com tick accent no topo e o texto de data/local deslizando da esquerda.
// Container do acervo VidMator (ref.: VidRush "date/location lower-third").
// Niche-agnostic: text / accent via props. Fundo transparente (composita sobre imagem).
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const DateLocationOverlay: React.FC<{
  text?: string;
  accent?: string;
}> = ({
  text = "July 2, 1984",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sp = spring({ frame, fps, config: { damping: 18, stiffness: 100 }, durationInFrames: 20 });
  const x = interpolate(sp, [0, 1], [-60, 0]);
  const op = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const barH = interpolate(sp, [0, 1], [0, 1]);
  const tickW = interpolate(frame, [8, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: SANS }}>
      <div
        style={{
          position: "absolute",
          left: 130,
          bottom: 150,
          display: "flex",
          alignItems: "center",
          opacity: op,
          transform: `translateX(${x}px)`,
        }}
      >
        <div
          style={{
            width: 8,
            height: 96 * barH,
            background: accent,
            borderRadius: 4,
            marginRight: 28,
            boxShadow: `0 0 16px ${accent}`,
          }}
        />
        <div
          style={{
            background: "rgba(10,11,15,0.72)",
            padding: "22px 40px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div style={{ width: tickW * 64, height: 4, background: accent, borderRadius: 2, marginBottom: 14 }} />
          <div style={{ fontSize: 58, fontWeight: 700, color: "#fff", letterSpacing: 1 }}>{text}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
