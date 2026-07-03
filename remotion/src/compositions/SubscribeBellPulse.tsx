import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT_GOLD, TEXT_PRIMARY } from "./_shared";

export const SubscribeBellPulse: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 24 });
  const translateY = (1 - enter) * 60;
  // Bell ring shake
  const bellShake = frame > 30 ? Math.sin(frame / 1.5) * 8 * Math.exp(-(frame - 30) / 25) : 0;
  // Thumb pulse
  const thumbPulse = 1 + Math.sin(frame / 5) * 0.1;
  const subPulse = 1 + Math.sin(frame / 8) * 0.04;
  return (
    <AbsoluteFill style={{ background: "transparent", justifyContent: "flex-end", alignItems: "center", paddingBottom: 60, gap: 24 }}>
      <div style={{ display: "flex", gap: 16, alignItems: "center", transform: `translateY(${translateY}px)`, opacity: enter, fontFamily: "system-ui, sans-serif" }}>
        <div
          style={{
            background: "#ff0000",
            color: "#ffffff",
            padding: "16px 40px",
            borderRadius: 8,
            fontWeight: 700,
            fontSize: 26,
            transform: `scale(${subPulse})`,
            boxShadow: "0 12px 40px rgba(255, 0, 0, 0.6)",
            letterSpacing: 0.5,
          }}
        >
          SUBSCRIBE
        </div>
        <div
          style={{
            width: 70,
            height: 70,
            borderRadius: "50%",
            background: "#222",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 36,
            transform: `rotate(${bellShake}deg)`,
            boxShadow: `0 0 30px ${ACCENT_GOLD}88`,
            border: `2px solid ${ACCENT_GOLD}`,
          }}
        >
          🔔
        </div>
        <div
          style={{
            width: 70,
            height: 70,
            borderRadius: "50%",
            background: "#222",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 36,
            transform: `scale(${thumbPulse})`,
            boxShadow: "0 0 30px rgba(78, 168, 245, 0.6)",
            border: "2px solid #4ea8f5",
          }}
        >
          👍
        </div>
      </div>
      <div style={{ color: TEXT_PRIMARY, fontSize: 18, opacity: enter * 0.85, fontFamily: "system-ui, sans-serif" }}>
        Like & Subscribe for more
      </div>
    </AbsoluteFill>
  );
};
