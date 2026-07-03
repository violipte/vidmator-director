import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";

// Schema permite editar props no Remotion Studio sem mexer no código.
export const ctaCardSchema = z.object({
  titulo: z.string(),
  subtitulo: z.string(),
  accentColor: z.string(),
});

type Props = z.infer<typeof ctaCardSchema>;

export const CtaCard: React.FC<Props> = ({ titulo, subtitulo, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Card entra com spring nos primeiros 20 frames
  const enter = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 110, mass: 0.6 },
    durationInFrames: 24,
  });

  // Sai com fade nos últimos 30 frames
  const exit = interpolate(
    frame,
    [durationInFrames - 30, durationInFrames],
    [1, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  const scale = interpolate(enter, [0, 1], [0.8, 1]);
  const opacity = enter * exit;
  const translateY = interpolate(enter, [0, 1], [40, 0]);

  // Pulse sutil no botão depois do card estar visível
  const pulse = Math.sin((frame / fps) * Math.PI * 2 * 1.2) * 0.04 + 1;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 120,
      }}
    >
      <div
        style={{
          background: "rgba(15, 17, 21, 0.92)",
          borderRadius: 24,
          padding: "32px 48px",
          minWidth: 720,
          display: "flex",
          alignItems: "center",
          gap: 28,
          boxShadow: `0 12px 48px rgba(0,0,0,0.5), 0 0 0 1px ${accentColor}33`,
          opacity,
          transform: `translateY(${translateY}px) scale(${scale})`,
          fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif",
        }}
      >
        <div
          style={{
            flex: 1,
            color: "#e4e6eb",
          }}
        >
          <div style={{ fontSize: 38, fontWeight: 700, lineHeight: 1.15 }}>
            {titulo}
          </div>
          <div style={{ fontSize: 22, color: "#8a8f9c", marginTop: 6, fontStyle: "italic" }}>
            {subtitulo}
          </div>
        </div>
        <div
          style={{
            background: accentColor,
            color: "#0f1115",
            padding: "16px 36px",
            borderRadius: 999,
            fontWeight: 700,
            fontSize: 22,
            letterSpacing: 0.3,
            transform: `scale(${pulse})`,
            whiteSpace: "nowrap",
          }}
        >
          GET IT →
        </div>
      </div>
    </AbsoluteFill>
  );
};
