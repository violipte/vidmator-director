import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM } from "./_shared";

export const CtaPopupCenter: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 13, stiffness: 100 }, durationInFrames: 30 });
  const exit = interpolate(frame, [durationInFrames - 25, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const opacity = enter * exit;
  const scale = interpolate(enter, [0, 1], [0.72, 1]);
  const backdropOp = enter * 0.65 * exit;
  return (
    <AbsoluteFill style={{ background: `rgba(5, 5, 15, ${backdropOp})`, backdropFilter: "blur(6px)", justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          width: 560,
          padding: 40,
          background: "rgba(20, 20, 30, 0.96)",
          borderRadius: 24,
          textAlign: "center",
          opacity,
          transform: `scale(${scale})`,
          boxShadow: `0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px ${ACCENT_GOLD}66`,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ fontSize: 38, marginBottom: 6 }}>🌟</div>
        <div style={{ color: TEXT_PRIMARY, fontSize: 32, fontWeight: 700, marginBottom: 10, fontFamily: "serif" }}>
          Get Your FREE Guide
        </div>
        <div style={{ color: TEXT_DIM, fontSize: 17, marginBottom: 24, lineHeight: 1.4 }}>
          The Starseed Awakening Codex<br />Available for the next 24 hours only
        </div>
        <div
          style={{
            display: "inline-block",
            background: ACCENT_GOLD,
            color: "#0f1115",
            padding: "14px 40px",
            borderRadius: 999,
            fontWeight: 700,
            fontSize: 18,
            letterSpacing: 0.5,
          }}
        >
          DOWNLOAD NOW →
        </div>
      </div>
    </AbsoluteFill>
  );
};
