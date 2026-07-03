import { AbsoluteFill, Img, Sequence, staticFile, interpolate, spring, Easing, useCurrentFrame, useVideoConfig } from "remotion";

// Imagens PD do caso (jornal/imprensa/registros) com ENTRADAS ÚNICAS.
// Estilos: photo (foto sobre fundo borrado, Ken Burns), split (2 imagens), clipping (recorte de jornal).

const FONT = "'Segoe UI', system-ui, sans-serif";
const ACCENT = "#facc15";

type Props = {
  estilo?: "photo" | "split" | "clipping";
  imagens: string[];        // rels (1 normalmente; 2 p/ split)
  legenda?: string | null;
  durFrames?: number;
  capFont?: string;         // fonte da legenda (tema por niche)
};

const Caption: React.FC<{ texto?: string | null; op: number; font?: string }> = ({ texto, op, font = FONT }) =>
  texto ? (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 70, textAlign: "center", opacity: op }}>
      <span style={{ background: "rgba(6,10,18,0.7)", color: "#fff", fontFamily: font, fontWeight: 600, fontSize: 28,
        padding: "10px 26px", borderRadius: 6, border: `1px solid ${ACCENT}`, letterSpacing: 0.5 }}>{texto}</span>
    </div>
  ) : null;

export const ImageCard: React.FC<Props> = ({ estilo = "photo", imagens, legenda, durFrames, capFont = FONT }) => {
  const frame = useCurrentFrame();
  const cfg = useVideoConfig();
  const total = durFrames || cfg.durationInFrames;
  const fps = cfg.fps;
  const img = (i: number) => staticFile(imagens[Math.min(i, imagens.length - 1)] || imagens[0]);
  const inAll = interpolate(frame, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const outAll = interpolate(frame, [total - 12, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const opacity = Math.min(inAll, outAll);
  const kb = interpolate(frame, [0, total], [1.0, 1.12]); // ken burns lento

  if (estilo === "split") {
    const lx = interpolate(spring({ frame, fps, config: { damping: 16 }, durationInFrames: 18 }), [0, 1], [-100, 0]);
    const rx = interpolate(spring({ frame: frame - 4, fps, config: { damping: 16 }, durationInFrames: 18 }), [0, 1], [100, 0]);
    return (
      <AbsoluteFill style={{ backgroundColor: "#05070d", opacity }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: "50%", height: "100%", overflow: "hidden", transform: `translateX(${lx}%)` }}>
          <Img src={img(0)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }} />
        </div>
        <div style={{ position: "absolute", right: 0, top: 0, width: "50%", height: "100%", overflow: "hidden", transform: `translateX(${rx}%)` }}>
          <Img src={img(1)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${kb})` }} />
        </div>
        <div style={{ position: "absolute", left: "50%", top: 0, width: 4, height: "100%", background: "#fff", transform: "translateX(-2px)", opacity: 0.85 }} />
        <Caption texto={legenda} op={opacity} font={capFont} />
      </AbsoluteFill>
    );
  }

  if (estilo === "clipping") {
    const sp = spring({ frame, fps, config: { damping: 12 }, durationInFrames: 20 });
    return (
      <AbsoluteFill style={{ backgroundColor: "#0a0d14", opacity }}>
        {/* fundo: cópia borrada */}
        <Img src={img(0)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: "blur(34px) brightness(0.4) saturate(0.6)" }} />
        <AbsoluteFill style={{ background: "rgba(5,8,14,0.45)" }} />
        {/* recorte de jornal */}
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ transform: `scale(${0.7 + 0.3 * sp}) rotate(${-3 + 3 * sp}deg)`, opacity: sp,
            background: "#f4efe2", padding: 14, boxShadow: "0 24px 60px rgba(0,0,0,0.7)", maxWidth: "62%" }}>
            <Img src={img(0)} style={{ display: "block", maxWidth: "100%", maxHeight: 760, objectFit: "contain", filter: "sepia(0.25) contrast(1.05)" }} />
            {legenda && <div style={{ color: "#2a2a2a", fontFamily: "Georgia, serif", fontSize: 24, fontWeight: 700, textAlign: "center", marginTop: 10 }}>{legenda}</div>}
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // photo: foto nítida sobre fundo borrado dela mesma + Ken Burns
  return (
    <AbsoluteFill style={{ backgroundColor: "#05070d", opacity }}>
      <Img src={img(0)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: "blur(40px) brightness(0.45) saturate(0.7)", transform: `scale(${kb * 1.1})` }} />
      <AbsoluteFill style={{ background: "rgba(5,8,14,0.35)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Img src={img(0)} style={{ maxWidth: "78%", maxHeight: "82%", objectFit: "contain", borderRadius: 4,
          border: "3px solid rgba(255,255,255,0.92)", boxShadow: "0 18px 60px rgba(0,0,0,0.7)", transform: `scale(${kb})` }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px 60px rgba(0,0,0,0.6)", pointerEvents: "none" }} />
      <Caption texto={legenda} op={opacity} font={capFont} />
    </AbsoluteFill>
  );
};

// Demo dos 3 estilos (clipping -> split -> photo)
export const ImageStyleDemo: React.FC = () => {
  const { fps } = useVideoConfig();
  const seg = Math.round(4 * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Sequence from={0} durationInFrames={seg}>
        <ImageCard estilo="clipping" imagens={["test/imgdemo/clip0.jpg"]} legenda="Illustrated Police News, 1888" durFrames={seg} />
      </Sequence>
      <Sequence from={seg} durationInFrames={seg}>
        <ImageCard estilo="split" imagens={["test/imgdemo/split0.jpg", "test/imgdemo/split1.jpg"]} legenda="Earhart e o Electra" durFrames={seg} />
      </Sequence>
      <Sequence from={seg * 2} durationInFrames={seg}>
        <ImageCard estilo="photo" imagens={["test/imgdemo/photo0.jpg"]} legenda="Manuscrito Voynich" durFrames={seg} />
      </Sequence>
    </AbsoluteFill>
  );
};
