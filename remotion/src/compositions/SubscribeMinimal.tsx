import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const SubscribeMinimal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 90 }, durationInFrames: 22 });
  const pulse = 1 + Math.sin(frame / 7) * 0.05;
  const ringPulse = Math.abs(Math.sin(frame / 12));
  return (
    <AbsoluteFill style={{ background: "transparent", justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", opacity: enter, transform: `scale(${0.7 + enter * 0.3})` }}>
        {/* Ring pulsando atrás do botão */}
        <div
          style={{
            position: "absolute",
            inset: -20,
            borderRadius: 999,
            border: "2px solid rgba(255, 0, 0, 0.5)",
            transform: `scale(${1 + ringPulse * 0.3})`,
            opacity: 1 - ringPulse,
            pointerEvents: "none",
          }}
        />
        <div
          style={{
            background: "#ff0000",
            color: "#ffffff",
            padding: "20px 56px",
            borderRadius: 999,
            fontWeight: 700,
            fontSize: 28,
            transform: `scale(${pulse})`,
            boxShadow: "0 16px 50px rgba(255, 0, 0, 0.55)",
            letterSpacing: 0.6,
            fontFamily: "system-ui, sans-serif",
          }}
        >
          SUBSCRIBE
        </div>
      </div>
    </AbsoluteFill>
  );
};
