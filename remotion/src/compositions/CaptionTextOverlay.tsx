import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// CAPTION TEXT OVERLAY — lower-third minimalista: risco accent que cresce + legenda
// centralizada em pill escura discreta, subindo com fade. Fundo transparente.
// Container do acervo VidMator (ref.: VidRush "minimal caption").
// Niche-agnostic: caption / accent via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const CaptionTextOverlay: React.FC<{
  caption?: string;
  accent?: string;
}> = ({
  caption = "Caption goes here",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sp = spring({ frame, fps, config: { damping: 20, stiffness: 100 }, durationInFrames: 20 });
  const y = interpolate(sp, [0, 1], [30, 0]);
  const op = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const lineW = interpolate(frame, [8, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: SANS, justifyContent: "flex-end", alignItems: "center" }}>
      <div style={{ marginBottom: 130, textAlign: "center", opacity: op, transform: `translateY(${y}px)` }}>
        <div
          style={{
            width: lineW * 90,
            height: 4,
            background: accent,
            borderRadius: 2,
            margin: "0 auto 22px",
            boxShadow: `0 0 14px ${accent}`,
          }}
        />
        <div
          style={{
            display: "inline-block",
            fontSize: 46,
            fontWeight: 500,
            color: "#fff",
            letterSpacing: 1,
            padding: "14px 40px",
            background: "rgba(10,11,15,0.6)",
            borderRadius: 8,
            textShadow: "0 2px 10px rgba(0,0,0,0.7)",
          }}
        >
          {caption}
        </div>
      </div>
    </AbsoluteFill>
  );
};
