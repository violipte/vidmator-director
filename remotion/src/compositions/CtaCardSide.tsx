import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT_GOLD, TEXT_PRIMARY, TEXT_DIM } from "./_shared";

export const CtaCardSide: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 15, stiffness: 110 }, durationInFrames: 28 });
  const exit = interpolate(frame, [durationInFrames - 28, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const opacity = enter * exit;
  const translateX = interpolate(enter, [0, 1], [-340, 0]);
  return (
    <AbsoluteFill style={{ background: "transparent", justifyContent: "center", paddingLeft: 60 }}>
      <div
        style={{
          width: 360,
          background: "rgba(15, 17, 21, 0.93)",
          borderRadius: 20,
          padding: 28,
          display: "flex",
          gap: 18,
          alignItems: "center",
          opacity,
          transform: `translateX(${translateX}px)`,
          boxShadow: `0 16px 48px rgba(0,0,0,0.55), 0 0 0 1px ${ACCENT_GOLD}44`,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {/* Mockup capa ebook */}
        <div
          style={{
            width: 86,
            height: 120,
            background: "linear-gradient(135deg, #1a1530 0%, #2a1850 100%)",
            border: `2px solid ${ACCENT_GOLD}`,
            borderRadius: 4,
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: ACCENT_GOLD,
            fontWeight: 700,
            fontSize: 11,
            textAlign: "center",
            padding: 6,
            boxShadow: "0 8px 24px rgba(0,0,0,0.6)",
          }}
        >
          STARSEED<br />GUIDE
        </div>
        <div>
          <div style={{ color: TEXT_PRIMARY, fontSize: 18, fontWeight: 700, lineHeight: 1.2 }}>
            FREE Guide
          </div>
          <div style={{ color: TEXT_DIM, fontSize: 13, marginTop: 4, lineHeight: 1.4 }}>
            Tap the link in description
          </div>
          <div style={{ marginTop: 12, color: ACCENT_GOLD, fontSize: 14, fontWeight: 700 }}>
            GET IT →
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
