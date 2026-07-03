import { AbsoluteFill, Img, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile, Easing } from "remotion";

// Galeria DEMO das 8 apresentações de imagem/vídeo (como o CLIPE se move).
// Cada slide aplica um template numa imagem real de exemplo + label. O Director escolherá
// o template por contexto. Default de produção = Ken Burns.

const W = 1920, H = 1080;
const FONT = "'Segoe UI', system-ui, sans-serif";
const ACCENT = "#fbbf24";
const IMGS = [
  staticFile("test/clips/scene_0.jpg"),
  staticFile("test/clips/scene_10.jpg"),
  staticFile("test/clips/scene_100.jpg"),
  staticFile("test/clips/scene_102.jpg"),
];
const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));

// 1) LUPA / GLASS INSPECT — uma lente ampliada passa sobre a imagem
const GlassInspect: React.FC<{ p: number }> = ({ p }) => {
  const cx = interpolate(p, [0, 1], [28, 72]), cy = 50 + Math.sin(p * Math.PI * 2) * 14, R = 175, Z = 2.1;
  return (
    <AbsoluteFill>
      <Img src={IMGS[0]} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.82) saturate(0.9)" }} />
      <div style={{
        position: "absolute", left: `calc(${cx}% - ${R}px)`, top: `calc(${cy}% - ${R}px)`, width: 2 * R, height: 2 * R,
        borderRadius: "50%", border: "4px solid rgba(255,255,255,0.95)", boxShadow: "0 0 0 3px rgba(0,0,0,0.5), 0 14px 40px rgba(0,0,0,0.6)",
        backgroundImage: `url(${IMGS[0]})`, backgroundSize: `${W * Z}px ${H * Z}px`,
        backgroundPosition: `-${(cx / 100) * W * Z - R}px -${(cy / 100) * H * Z - R}px`,
      }} />
    </AbsoluteFill>
  );
};

// 2) SPOTLIGHT — escurece tudo menos um foco que se move
const Spotlight: React.FC<{ p: number }> = ({ p }) => {
  const cx = interpolate(p, [0, 1], [34, 66]), cy = 50 + Math.sin(p * Math.PI * 2) * 11;
  return (
    <AbsoluteFill>
      <Img src={IMGS[2]} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <AbsoluteFill style={{ background: `radial-gradient(circle 280px at ${cx}% ${cy}%, transparent 0%, rgba(0,0,0,0.2) 40%, rgba(0,0,0,0.86) 72%)` }} />
    </AbsoluteFill>
  );
};

// 3) SPLIT / TWO-IMAGE — divisor móvel (antes/depois)
const Split: React.FC<{ p: number }> = ({ p }) => {
  const x = 50 + Math.sin(seg(p, 0.1, 0.95) * Math.PI) * 22;
  return (
    <AbsoluteFill>
      <Img src={IMGS[0]} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${x}%)` }}>
        <Img src={IMGS[1]} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: `${x}%`, top: 0, width: 4, height: "100%", background: "#fff", boxShadow: "0 0 14px rgba(0,0,0,0.6)" }} />
      <div style={{ position: "absolute", left: `calc(${x}% - 26px)`, top: "calc(50% - 26px)", width: 52, height: 52, borderRadius: "50%", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT, fontWeight: 900, color: "#0b1020", fontSize: 22 }}>⟷</div>
    </AbsoluteFill>
  );
};

// 4) PHOTO GRID — 4 imagens montam um mosaico (entrada escalonada)
const PhotoGrid: React.FC<{ p: number; frame: number; fps: number }> = ({ frame, fps }) => (
  <AbsoluteFill style={{ background: "#0b1020", display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: 10, padding: 10 }}>
    {IMGS.map((im, i) => {
      const sp = spring({ frame: frame - i * 7, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 18 });
      return <div key={i} style={{ overflow: "hidden", borderRadius: 8, opacity: sp, transform: `scale(${0.7 + sp * 0.3})` }}>
        <Img src={im} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>;
    })}
  </AbsoluteFill>
);

// 5) POLAROID / MOLDURA — foto emoldurada que cai e gira
const Polaroid: React.FC<{ p: number; frame: number; fps: number }> = ({ frame, fps }) => {
  const sp = spring({ frame, fps, config: { damping: 12, stiffness: 90 }, durationInFrames: 26 });
  const rot = interpolate(sp, [0, 1], [-9, -3]), ty = interpolate(sp, [0, 1], [-70, 0]);
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #1a2230, #080c14)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ background: "#f4f1ea", padding: "22px 22px 70px", borderRadius: 4, boxShadow: "0 30px 70px rgba(0,0,0,0.7)", transform: `translateY(${ty}px) rotate(${rot}deg) scale(${0.9 + sp * 0.1})`, opacity: sp }}>
        <Img src={IMGS[3]} style={{ width: 760, height: 560, objectFit: "cover" }} />
        <div style={{ fontFamily: "'Bradley Hand','Segoe Script',cursive", fontSize: 34, color: "#2a2a2a", textAlign: "center", marginTop: 18 }}>— a memory —</div>
      </div>
    </AbsoluteFill>
  );
};

// 6) FILM FRAME — moldura de filme antigo + tremor + grão
const FilmFrame: React.FC<{ p: number; frame: number }> = ({ frame }) => {
  const jx = Math.sin(frame * 1.7) * 2, jy = Math.cos(frame * 2.3) * 2;
  const holes = Array.from({ length: 9 });
  return (
    <AbsoluteFill style={{ background: "#000", justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", width: 1500, height: 844, transform: `translate(${jx}px, ${jy}px)`, background: "#111" }}>
        <Img src={IMGS[2]} style={{ position: "absolute", inset: "0 70px", width: "calc(100% - 140px)", height: "100%", objectFit: "cover", filter: "sepia(0.35) contrast(1.1) brightness(0.95) saturate(0.8)" }} />
        {[12, 1428].map((lx, s) => holes.map((_, i) => (
          <div key={`${s}-${i}`} style={{ position: "absolute", left: lx, top: 18 + i * 92, width: 44, height: 60, background: "#000", borderRadius: 6, border: "2px solid #1c1c1c" }} />
        )))}
        <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0 2px, transparent 2px 4px)", pointerEvents: "none", opacity: 0.5 }} />
      </div>
    </AbsoluteFill>
  );
};

// 7) PARALLAX — pseudo-profundidade: fundo dá zoom, vinheta/luz desliza ao contrário
const Parallax: React.FC<{ p: number }> = ({ p }) => {
  const z = 1.12 + p * 0.16, fg = interpolate(p, [0, 1], [26, -26]);
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img src={IMGS[0]} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z}) translateX(${-fg * 0.35}px)` }} />
      <AbsoluteFill style={{ transform: `translateX(${fg}px)`, background: "radial-gradient(ellipse 70% 90% at 50% 50%, transparent 40%, rgba(0,0,0,0.55) 100%)" }} />
      <AbsoluteFill style={{ transform: `translateX(${fg * 1.6}px)`, background: "linear-gradient(105deg, transparent 60%, rgba(255,210,120,0.12) 78%, transparent 90%)" }} />
    </AbsoluteFill>
  );
};

// 8) LAYERED REVEAL — imagem revelada (cinza→cor) por uma faixa que varre
const LayeredReveal: React.FC<{ p: number }> = ({ p }) => {
  const w = interpolate(seg(p, 0.1, 0.85), [0, 1], [0, 100]);
  return (
    <AbsoluteFill>
      <Img src={IMGS[1]} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) brightness(0.45)" }} />
      <AbsoluteFill style={{ clipPath: `inset(0 ${100 - w}% 0 0)` }}>
        <Img src={IMGS[1]} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: `${w}%`, top: 0, width: 6, height: "100%", background: "linear-gradient(90deg, transparent, #fff)", boxShadow: `0 0 26px 6px ${ACCENT}`, opacity: w > 1 && w < 99 ? 1 : 0 }} />
    </AbsoluteFill>
  );
};

const SLIDES: { nome: string; uso: string; comp: React.FC<any> }[] = [
  { nome: "Lupa / Glass Inspect", uso: "documento, rosto, mapa, pista", comp: GlassInspect },
  { nome: "Spotlight Focus", uso: "dirigir o olhar, suspense", comp: Spotlight },
  { nome: "Split / Two-Image", uso: "comparação, antes/depois", comp: Split },
  { nome: "Photo Grid / Collage", uso: "coleção, montagem, 'vários'", comp: PhotoGrid },
  { nome: "Polaroid / Moldura", uso: "histórico, evidência, memória", comp: Polaroid },
  { nome: "Film / VHS Frame", uso: "época, found-footage", comp: FilmFrame },
  { nome: "Parallax", uso: "dar profundidade 3D a foto", comp: Parallax },
  { nome: "Layered Reveal", uso: "revelação dramática", comp: LayeredReveal },
];

const SLIDE = 105; // 3.5s cada

const Slide: React.FC<{ i: number }> = ({ i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [4, SLIDE - 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const op = Math.min(interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" }), interpolate(frame, [SLIDE - 8, SLIDE], [1, 0], { extrapolateLeft: "clamp" }));
  const s = SLIDES[i], C = s.comp;
  return (
    <AbsoluteFill style={{ opacity: op, background: "#000" }}>
      <C p={p} frame={frame} fps={fps} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 46, display: "flex", justifyContent: "center" }}>
        <div style={{ background: "rgba(8,12,20,0.86)", borderRadius: 14, padding: "14px 30px", display: "flex", alignItems: "center", gap: 16, boxShadow: "0 12px 36px rgba(0,0,0,0.6)" }}>
          <span style={{ color: ACCENT, fontFamily: FONT, fontWeight: 900, fontSize: 30 }}>{i + 1}.</span>
          <span style={{ color: "#fff", fontFamily: FONT, fontWeight: 800, fontSize: 32 }}>{s.nome}</span>
          <span style={{ color: "#9fb0c4", fontFamily: FONT, fontSize: 24 }}>· {s.uso}</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const PresentationGallery: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    {SLIDES.map((_, i) => (
      <Sequence key={i} from={i * SLIDE} durationInFrames={SLIDE}>
        <Slide i={i} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
