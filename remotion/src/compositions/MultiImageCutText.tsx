import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

// MULTI IMAGE CUT TEXT — cada foto em tela cheia (com overlay escuro) + um TÍTULO grande,
// cortando (hard cut) de uma pra outra em sequência. Container do acervo VidMator.
// Niche-agnostic: items[{image,title}]/accent via props.
const DISPLAY = "'Archivo Black', 'Impact', 'Arial Black', sans-serif";

type Item = { image: string; title: string };

export const MultiImageCutText: React.FC<{
  items?: Item[];
  accent?: string;
}> = ({
  items = [
    { image: "test/clips/scene_10.jpg", title: "2-0" },
    { image: "test/clips/scene_100.jpg", title: "Brazil Win" },
    { image: "test/clips/scene_101.jpg", title: "Portugal" },
    { image: "test/clips/scene_102.jpg", title: "Argentina" },
  ],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const list = items.length ? items : [{ image: "test/clips/scene_10.jpg", title: "One" }];
  const per = durationInFrames / list.length;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {list.map((it, i) => {
        const start = i * per;
        const local = frame - start;
        // hard cut: só mostra a foto do segmento atual
        if (local < 0 || local >= per) return null;

        const kb = interpolate(local, [0, per], [1.08, 1.16]); // ken burns dentro do corte
        const tPop = spring({ frame: local - 3, fps, config: { damping: 13, stiffness: 120 }, durationInFrames: 16 });
        const tY = interpolate(tPop, [0, 1], [60, 0]);
        const tOp = interpolate(local, [3, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const barW = interpolate(local, [0, per], [0, 100], { extrapolateRight: "clamp" });

        return (
          <AbsoluteFill key={i}>
            <Img
              src={staticFile(it.image)}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }}
            />
            {/* overlay p/ legibilidade */}
            <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.15) 45%, rgba(0,0,0,0.82) 100%)" }} />

            {/* título grande */}
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 150 }}>
              <div
                style={{
                  fontFamily: DISPLAY,
                  fontSize: 128,
                  color: "#fff",
                  textTransform: "uppercase",
                  letterSpacing: 1,
                  textAlign: "center",
                  lineHeight: 1.02,
                  opacity: tOp,
                  transform: `translateY(${tY}px)`,
                  textShadow: `0 8px 34px rgba(0,0,0,0.8), 0 0 40px ${accent}55`,
                  padding: "0 60px",
                }}
              >
                {it.title}
              </div>
              <div
                style={{
                  marginTop: 26,
                  width: 160,
                  height: 8,
                  borderRadius: 4,
                  background: accent,
                  boxShadow: `0 0 22px ${accent}`,
                  opacity: tOp,
                }}
              />
            </AbsoluteFill>

            {/* barra de progresso do segmento */}
            <div style={{ position: "absolute", left: 0, bottom: 0, width: `${barW}%`, height: 8, background: accent, boxShadow: `0 0 18px ${accent}` }} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
