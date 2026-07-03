import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_A_COLOR, SCENE_B_COLOR, TEXT_PRIMARY } from "./_shared";

export const CrossfadeTransition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const half = durationInFrames / 2;
  const opacityB = interpolate(frame, [half - 15, half + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_A_COLOR, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE A</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_B_COLOR, opacity: opacityB, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE B</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
