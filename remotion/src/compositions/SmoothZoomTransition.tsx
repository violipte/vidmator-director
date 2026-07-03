import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { SCENE_A_COLOR, SCENE_B_COLOR, TEXT_PRIMARY } from "./_shared";

export const SmoothZoomTransition: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const half = durationInFrames / 2;
  // Cena A zooma in até desaparecer, cena B aparece com leve zoom out (Hitchcock dolly)
  const scaleA = interpolate(frame, [0, half + 10], [1, 2.5], { extrapolateRight: "clamp" });
  const opacityA = interpolate(frame, [half - 10, half + 10], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scaleB = interpolate(frame, [half - 10, durationInFrames], [1.3, 1], { extrapolateLeft: "clamp" });
  const opacityB = interpolate(frame, [half - 10, half + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_A_COLOR, transform: `scale(${scaleA})`, opacity: opacityA, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE A</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: SCENE_B_COLOR, transform: `scale(${scaleB})`, opacity: opacityB, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: TEXT_PRIMARY, fontSize: 96, fontWeight: 700, fontFamily: "serif" }}>SCENE B</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
