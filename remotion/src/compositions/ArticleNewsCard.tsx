import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// ARTICLE NEWS CARD — card de NOTÍCIA: imagem no topo (com caption) + corpo de texto;
// o highlightText recebe uma MARCA (highlighter) accent. Corpo entra com fade/slide.
// Container do acervo VidMator (ref.: VidRush "citação de artigo/fonte"). Niche-agnostic via props.
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SERIF = "'Georgia','Times New Roman',serif";
const SANS = "'Inter','Segoe UI',sans-serif";

export const ArticleNewsCard: React.FC<{
  articleImage?: string;
  articleText?: string;
  highlightText?: string;
  imageCaption?: string;
  accent?: string;
}> = ({
  articleImage = "test/clips/scene_10.jpg",
  articleText = "An FBI official tells our reporter the truth about the case.",
  highlightText = "FBI official",
  imageCaption = "Photo credit: Unsplash",
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardIn = spring({ frame, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 24 });
  const imgIn = interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const textIn = spring({ frame: frame - 20, fps, config: { damping: 20, stiffness: 80 }, durationInFrames: 22 });
  const hlWidth = interpolate(frame, [40, 62], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // parte o texto no highlightText (1ª ocorrência) p/ aplicar a marca accent
  const idx = highlightText ? articleText.indexOf(highlightText) : -1;
  const pre = idx >= 0 ? articleText.slice(0, idx) : articleText;
  const hl = idx >= 0 ? articleText.slice(idx, idx + highlightText.length) : "";
  const post = idx >= 0 ? articleText.slice(idx + highlightText.length) : "";

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 30%, #14161c 0%, #0a0b0f 72%)",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: SANS,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        }}
      />

      <div
        style={{
          width: 1160,
          borderRadius: 16,
          overflow: "hidden",
          background: "#14161c",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          opacity: cardIn,
          transform: `translateY(${(1 - cardIn) * 60}px) scale(${0.96 + 0.04 * cardIn})`,
        }}
      >
        {/* faixa "NEWS" */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "20px 34px 0" }}>
          <div
            style={{
              background: accent,
              color: "#0a0b0f",
              fontFamily: DISPLAY,
              fontSize: 22,
              letterSpacing: 3,
              padding: "6px 16px",
              borderRadius: 6,
            }}
          >
            NEWS
          </div>
          <div style={{ height: 3, flex: 1, background: `linear-gradient(90deg, ${accent}, transparent)` }} />
        </div>

        {/* imagem topo + caption */}
        <div style={{ padding: "20px 34px 0" }}>
          <div style={{ position: "relative", width: "100%", height: 480, borderRadius: 12, overflow: "hidden", opacity: imgIn }}>
            <Img
              src={staticFile(articleImage)}
              style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1.06 - 0.06 * imgIn})` }}
            />
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                padding: "26px 20px 12px",
                background: "linear-gradient(transparent, rgba(0,0,0,0.75))",
                color: "#9aa4b2",
                fontSize: 20,
                fontStyle: "italic",
              }}
            >
              {imageCaption}
            </div>
          </div>
        </div>

        {/* corpo de texto */}
        <div
          style={{
            padding: "28px 44px 42px",
            opacity: textIn,
            transform: `translateY(${(1 - textIn) * 24}px)`,
          }}
        >
          <p style={{ margin: 0, fontFamily: SERIF, fontSize: 52, lineHeight: 1.35, color: "#ffffff" }}>
            {pre}
            {hl && (
              <span style={{ position: "relative", display: "inline", color: "#0a0b0f", whiteSpace: "nowrap" }}>
                <span
                  style={{
                    position: "absolute",
                    left: -4,
                    right: -4,
                    top: "12%",
                    bottom: "8%",
                    width: `${hlWidth}%`,
                    background: accent,
                    borderRadius: 4,
                    zIndex: 0,
                  }}
                />
                <span style={{ position: "relative", zIndex: 1, color: hlWidth > 6 ? "#0a0b0f" : "#ffffff", fontWeight: 700 }}>{hl}</span>
              </span>
            )}
            {post}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};
