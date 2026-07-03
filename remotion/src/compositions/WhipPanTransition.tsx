import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_A_COLOR, SCENE_B_COLOR, TEXT_PRIMARY } from "./_shared";

export const WhipPanTransition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();
  const center = durationInFrames / 2;
  // Movimento rápido com blur acentuado no centro
  const progress = interpolate(frame, [center - 6, center + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const blurAmount = interpolate(frame, [center - 6, center, center + 6], [0, 40, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const offsetA = interpolate(progress, [0, 1], [0, -width * 1.2]);
  const offsetB = interpolate(progress, [0, 1], [width * 1.2, 0]);
  return (
    <AbsoluteFill style={{ filter: `blur(${blurAmount}px)` }}>
      <AbsoluteFill style={{ background: SCENE_A_COLOR, transform: `translateX(${offsetA}px)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE A</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_B_COLOR, transform: `translateX(${offsetB}px)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE B</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
