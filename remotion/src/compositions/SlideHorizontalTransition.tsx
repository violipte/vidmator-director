import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_A_COLOR, SCENE_B_COLOR, TEXT_PRIMARY } from "./_shared";

export const SlideHorizontalTransition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps, width } = useVideoConfig();
  const trigger = durationInFrames / 2 - 15;
  const t = spring({ frame: frame - trigger, fps, config: { damping: 18, stiffness: 100, mass: 0.8 }, durationInFrames: 30 });
  const offsetA = interpolate(t, [0, 1], [0, -width]);
  const offsetB = interpolate(t, [0, 1], [width, 0]);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_A_COLOR, transform: `translateX(${offsetA}px)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE A</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_B_COLOR, transform: `translateX(${offsetB}px)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE B</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
