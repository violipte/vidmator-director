import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT_GOLD } from "./_shared";

export const CtaBannerSlim: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 26 });
  const translateY = interpolate(enter, [0, 1], [80, 0]);
  const pulse = 1 + Math.sin(frame / 6) * 0.04;
  return (
    <AbsoluteFill style={{ background: "transparent", justifyContent: "flex-end", alignItems: "center", paddingBottom: 24 }}>
      <div
        style={{
          background: "rgba(15, 17, 21, 0.96)",
          backdropFilter: "blur(10px)",
          borderRadius: 999,
          padding: "14px 28px",
          display: "flex",
          alignItems: "center",
          gap: 18,
          transform: `translateY(${translateY}px)`,
          boxShadow: `0 8px 28px rgba(0,0,0,0.55), 0 0 0 1px ${ACCENT_GOLD}55`,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ color: "#e4e6eb", fontSize: 17, fontWeight: 600 }}>
          🌟 Free Starseed Guide — Link in Description
        </div>
        <div
          style={{
            background: ACCENT_GOLD,
            color: "#0f1115",
            padding: "8px 18px",
            borderRadius: 999,
            fontSize: 14,
            fontWeight: 700,
            transform: `scale(${pulse})`,
            letterSpacing: 0.4,
          }}
        >
          GET IT
        </div>
      </div>
    </AbsoluteFill>
  );
};
