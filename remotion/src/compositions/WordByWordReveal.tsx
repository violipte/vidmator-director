import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT_GOLD, TEXT_PRIMARY } from "./_shared";

const PHRASE = ["You", "Were", "Chosen", "Before", "Time"];

export const WordByWordReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #1a0e2e 0%, #050510 100%)", display: "flex", alignItems: "center", justifyContent: "center", gap: 24, fontFamily: "Georgia, serif" }}>
      {PHRASE.map((word, i) => {
        const delay = i * 8;
        const t = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 110, mass: 0.7 }, durationInFrames: 24 });
        const translateY = (1 - t) * 30;
        const opacity = t;
        const highlight = word === "Chosen";
        return (
          <span
            key={i}
            style={{
              color: highlight ? ACCENT_GOLD : TEXT_PRIMARY,
              fontSize: 78,
              fontWeight: 700,
              opacity,
              transform: `translateY(${translateY}px)`,
              textShadow: highlight ? `0 0 30px ${ACCENT_GOLD}` : "0 0 20px rgba(255,255,255,0.2)",
              letterSpacing: 1,
            }}
          >
            {word}
          </span>
        );
      })}
    </AbsoluteFill>
  );
};
