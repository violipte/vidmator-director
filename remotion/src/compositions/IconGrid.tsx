import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Icon } from "./_icons";

// ICON GRID — texto central + 4 ícones SVG em LOSANGO (topo/dir/base/esq) com linhas
// conectando (stroke-dashoffset) e entrada escalonada. Container do acervo VidMator.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const IconGrid: React.FC<{
  mainText?: string;
  topIcon?: string;
  rightIcon?: string;
  bottomIcon?: string;
  leftIcon?: string;
  accent?: string;
}> = ({
  mainText = "A Virtuous Circle",
  topIcon = "globe",
  rightIcon = "users",
  bottomIcon = "rocket",
  leftIcon = "heart",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const r = 300;
  const pts = [
    { x: cx, y: cy - r, icon: topIcon, delay: 14 },
    { x: cx + r * 1.15, y: cy, icon: rightIcon, delay: 22 },
    { x: cx, y: cy + r, icon: bottomIcon, delay: 30 },
    { x: cx - r * 1.15, y: cy, icon: leftIcon, delay: 38 },
  ];

  const draw = interpolate(frame, [6, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const path = `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y} L ${pts[2].x} ${pts[2].y} L ${pts[3].x} ${pts[3].y} Z`;

  const textOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const textScale = interpolate(
    spring({ frame, fps, config: { damping: 18, stiffness: 90 }, durationInFrames: 20 }),
    [0, 1],
    [0.8, 1]
  );

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", fontFamily: SANS }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <path
          d={path}
          fill="none"
          stroke={accent}
          strokeWidth={4}
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - draw}
          opacity={0.7}
          style={{ filter: `drop-shadow(0 0 10px ${accent}aa)` }}
        />
      </svg>

      {/* texto central */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            width: 380,
            textAlign: "center",
            fontFamily: DISPLAY,
            fontSize: 58,
            fontWeight: 900,
            color: "#fff",
            opacity: textOp,
            transform: `scale(${textScale})`,
            textShadow: `0 0 26px ${accent}55`,
            lineHeight: 1.1,
          }}
        >
          {mainText}
        </div>
      </AbsoluteFill>

      {/* ícones em losango */}
      {pts.map((p, i) => {
        const e = spring({ frame: frame - p.delay, fps, config: { damping: 12, stiffness: 130 }, durationInFrames: 16 });
        const s = interpolate(e, [0, 1], [0, 1]);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              transform: `translate(-50%, -50%) scale(${s})`,
              width: 150,
              height: 150,
              borderRadius: "50%",
              background: "#14161c",
              border: `2px solid ${accent}`,
              boxShadow: `0 0 30px ${accent}55, 0 16px 40px rgba(0,0,0,0.6)`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name={p.icon} color={accent} size={74} strokeWidth={1.8} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
