import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// POLL SURVEY BAR — card CLARO: pergunta (keyword destacada com accent) + barra horizontal
// dividida Yes/No enchendo até primaryPercentage% (marcas 0/50/100) + source pequeno embaixo.
// Container do acervo VidMator. Niche-agnostic via props.
const SANS = "'Inter', 'Segoe UI', sans-serif";

export const PollSurveyBar: React.FC<{
  question?: string;
  highlightedKeyword?: string;
  primaryLabel?: string;
  secondaryLabel?: string;
  primaryPercentage?: number;
  sourceText?: string;
  accent?: string;
}> = ({
  question = "Is a third party needed?",
  highlightedKeyword = "third party",
  primaryLabel = "Yes",
  secondaryLabel = "No",
  primaryPercentage = 62,
  sourceText = "Source: Gallup, October 2023",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cardE = spring({ frame, fps, config: { damping: 18, stiffness: 85 }, durationInFrames: 22 });
  const cardOp = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const cardScale = interpolate(cardE, [0, 1], [0.9, 1]);

  const fill = interpolate(frame, [20, 55], [0, primaryPercentage], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const secPct = 100 - primaryPercentage;
  const srcOp = interpolate(frame, [56, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const renderQuestion = () => {
    const idx = highlightedKeyword ? question.toLowerCase().indexOf(highlightedKeyword.toLowerCase()) : -1;
    if (idx < 0) return question;
    return (
      <>
        {question.slice(0, idx)}
        <span style={{ color: accent }}>{question.slice(idx, idx + highlightedKeyword.length)}</span>
        {question.slice(idx + highlightedKeyword.length)}
      </>
    );
  };

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: SANS }}>
      <div
        style={{
          transform: `scale(${cardScale})`,
          opacity: cardOp,
          background: "#f6f7f9",
          borderRadius: 20,
          boxShadow: "0 24px 70px rgba(0,0,0,0.5)",
          padding: "60px 70px",
          width: 1180,
        }}
      >
        <div style={{ fontSize: 62, fontWeight: 800, color: "#14161c", marginBottom: 44, lineHeight: 1.15 }}>
          {renderQuestion()}
        </div>

        {/* barra Yes/No */}
        <div style={{ display: "flex", height: 96, borderRadius: 14, overflow: "hidden", boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}>
          <div
            style={{
              width: `${fill}%`,
              background: accent,
              display: "flex",
              alignItems: "center",
              paddingLeft: 28,
              color: "#0a0b0f",
              fontWeight: 800,
              fontSize: 40,
              whiteSpace: "nowrap",
              overflow: "hidden",
            }}
          >
            {primaryLabel} {Math.round(fill)}%
          </div>
          <div
            style={{
              flex: 1,
              background: "#d7dbe2",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              paddingRight: 28,
              color: "#5b6472",
              fontWeight: 800,
              fontSize: 40,
              whiteSpace: "nowrap",
            }}
          >
            {secondaryLabel} {secPct}%
          </div>
        </div>

        {/* marcas de escala 0 / 50 / 100 */}
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, color: "#9aa4b2", fontSize: 26, fontWeight: 600 }}>
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </div>

        <div style={{ marginTop: 30, color: "#9aa4b2", fontSize: 26, opacity: srcOp }}>{sourceText}</div>
      </div>
    </AbsoluteFill>
  );
};
