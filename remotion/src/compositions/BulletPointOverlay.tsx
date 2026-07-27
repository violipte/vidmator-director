import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// BULLET POINT OVERLAY — painel escuro com bullets (marcador accent losango) aparecendo
// 1 a 1 com slide lateral. Container do acervo VidMator. Niche-agnostic: bullets[]/accent via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const BulletPointOverlay: React.FC<{
  bullets?: string[];
  accent?: string;
}> = ({
  bullets = ["First point", "Second point", "Third point"],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const panelE = spring({ frame, fps, config: { damping: 18, stiffness: 85 }, durationInFrames: 22 });
  const panelOp = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const panelX = interpolate(panelE, [0, 1], [-80, 0]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-start", fontFamily: SANS, paddingLeft: 160 }}>
      <div
        style={{
          transform: `translateX(${panelX}px)`,
          opacity: panelOp,
          background: "#14161c",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 16,
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          padding: "56px 64px",
          minWidth: 900,
          maxWidth: 1300,
        }}
      >
        {bullets.map((b, i) => {
          const delay = 14 + i * 14;
          const e = spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 100 }, durationInFrames: 18 });
          const op = interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const x = interpolate(e, [0, 1], [50, 0]);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 28,
                opacity: op,
                transform: `translateX(${x}px)`,
                margin: i === 0 ? 0 : "34px 0 0",
              }}
            >
              <div
                style={{
                  flex: "0 0 auto",
                  width: 26,
                  height: 26,
                  borderRadius: 6,
                  background: accent,
                  boxShadow: `0 0 18px ${accent}aa`,
                  transform: "rotate(45deg)",
                }}
              />
              <div style={{ fontSize: 52, fontWeight: 600, color: "#fff", lineHeight: 1.2 }}>{b}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
