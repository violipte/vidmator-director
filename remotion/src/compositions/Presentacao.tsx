import { AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile, Easing } from "remotion";

// Renderizador de PRODUÇÃO das apresentações de imagem (substitui o Ken Burns quando o Director
// escolhe um template por contexto). Single-image: lupa/spotlight/polaroid/film/parallax/reveal.
// Multi-image: split/grid (usa `extras`; se faltar, cai pra Ken Burns). Animação no ritmo da CENA.

export type PresentacaoSpec = {
  tipo: "lupa" | "spotlight" | "split" | "grid" | "polaroid" | "film" | "parallax" | "reveal" | "kenburns";
  extras?: string[] | null;   // rels extra (split: +1, grid: +3)
  foco?: [number, number] | null; // ponto de foco 0-100 p/ lupa/spotlight (default centro-baixo)
  legenda?: string | null;    // polaroid
};

const W = 1920, H = 1080;
const ACCENT = "#fbbf24";
const seg = (p: number, a: number, b: number) => Math.min(1, Math.max(0, (p - a) / (b - a)));

const KenBurns: React.FC<{ src: string; f: string; frame: number }> = ({ src, f, frame }) => {
  const kb = 1.04 + 0.12 * Math.min(1, frame / 300);
  return <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f, transform: `scale(${kb.toFixed(4)})` }} />;
};

export const Presentacao: React.FC<{ spec: PresentacaoSpec; rel: string; sceneFrames: number; vfilter?: string }> = ({ spec, rel, sceneFrames, vfilter = "none" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const src = staticFile(rel);
  const f = vfilter === "none" ? "" : vfilter;
  const pp = Math.min(1, frame / Math.max(sceneFrames, 1)); // 0->1 ao longo da cena (movimento lento)
  const fx = spec.foco?.[0] ?? 50, fy = spec.foco?.[1] ?? 58;

  switch (spec.tipo) {
    case "lupa": {
      const cx = fx + Math.sin(pp * Math.PI * 1.3) * 14, cy = fy + Math.cos(pp * Math.PI * 1.1) * 9, R = 175, Z = 2.1;
      return (
        <AbsoluteFill>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: `${f} brightness(0.82)`.trim() }} />
          <div style={{
            position: "absolute", left: `calc(${cx}% - ${R}px)`, top: `calc(${cy}% - ${R}px)`, width: 2 * R, height: 2 * R,
            borderRadius: "50%", border: "4px solid rgba(255,255,255,0.95)", boxShadow: "0 0 0 3px rgba(0,0,0,0.5), 0 14px 40px rgba(0,0,0,0.6)",
            backgroundImage: `url(${src})`, backgroundSize: `${W * Z}px ${H * Z}px`,
            backgroundPosition: `-${(cx / 100) * W * Z - R}px -${(cy / 100) * H * Z - R}px`,
          }} />
        </AbsoluteFill>
      );
    }
    case "spotlight": {
      const cx = fx + Math.sin(pp * Math.PI * 1.4) * 12, cy = fy + Math.cos(pp * Math.PI) * 8;
      return (
        <AbsoluteFill>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f }} />
          <AbsoluteFill style={{ background: `radial-gradient(circle 300px at ${cx}% ${cy}%, transparent 0%, rgba(0,0,0,0.25) 42%, rgba(0,0,0,0.85) 74%)` }} />
        </AbsoluteFill>
      );
    }
    case "parallax": {
      const z = 1.12 + pp * 0.16, fg = interpolate(pp, [0, 1], [22, -22]);
      return (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f, transform: `scale(${z}) translateX(${-fg * 0.35}px)` }} />
          <AbsoluteFill style={{ transform: `translateX(${fg}px)`, background: "radial-gradient(ellipse 70% 90% at 50% 50%, transparent 40%, rgba(0,0,0,0.5) 100%)" }} />
        </AbsoluteFill>
      );
    }
    case "reveal": {
      const w = interpolate(seg(pp, 0.04, 0.5), [0, 1], [0, 100]);
      return (
        <AbsoluteFill>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) brightness(0.45)" }} />
          <AbsoluteFill style={{ clipPath: `inset(0 ${100 - w}% 0 0)` }}>
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f, transform: `scale(${1.04 + pp * 0.06})` }} />
          </AbsoluteFill>
          {w > 1 && w < 99 && <div style={{ position: "absolute", left: `${w}%`, top: 0, width: 6, height: "100%", background: "linear-gradient(90deg, transparent, #fff)", boxShadow: `0 0 26px 6px ${ACCENT}` }} />}
        </AbsoluteFill>
      );
    }
    case "polaroid": {
      const sp = spring({ frame, fps, config: { damping: 12, stiffness: 90 }, durationInFrames: 26 });
      const rot = interpolate(sp, [0, 1], [-9, -3]) + Math.sin(pp * Math.PI) * 1.2, ty = interpolate(sp, [0, 1], [-70, 0]);
      const kb = 1.0 + pp * 0.05;
      return (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #1a2230, #070b12)", justifyContent: "center", alignItems: "center" }}>
          <div style={{ background: "#f4f1ea", padding: "22px 22px 70px", borderRadius: 4, boxShadow: "0 30px 70px rgba(0,0,0,0.7)", transform: `translateY(${ty}px) rotate(${rot}deg) scale(${0.9 + sp * 0.1})`, opacity: sp }}>
            <div style={{ width: 820, height: 600, overflow: "hidden" }}>
              <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f, transform: `scale(${kb.toFixed(3)})` }} />
            </div>
            {spec.legenda ? <div style={{ fontFamily: "'Bradley Hand','Segoe Script',cursive", fontSize: 34, color: "#2a2a2a", textAlign: "center", marginTop: 18 }}>{spec.legenda}</div> : <div style={{ height: 8 }} />}
          </div>
        </AbsoluteFill>
      );
    }
    case "film": {
      const jx = Math.sin(frame * 1.7) * 2, jy = Math.cos(frame * 2.3) * 2, kb = 1.02 + pp * 0.06;
      const holes = Array.from({ length: 9 });
      return (
        <AbsoluteFill style={{ background: "#000", justifyContent: "center", alignItems: "center" }}>
          <div style={{ position: "relative", width: 1500, height: 844, transform: `translate(${jx}px, ${jy}px)`, background: "#111" }}>
            <div style={{ position: "absolute", inset: "0 70px", overflow: "hidden" }}>
              <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: `${f} sepia(0.3) contrast(1.1) brightness(0.95) saturate(0.8)`.trim(), transform: `scale(${kb.toFixed(3)})` }} />
            </div>
            {[12, 1444].map((lx, s) => holes.map((_, i) => (
              <div key={`${s}-${i}`} style={{ position: "absolute", left: lx, top: 18 + i * 92, width: 44, height: 60, background: "#000", borderRadius: 6, border: "2px solid #1c1c1c" }} />
            )))}
            <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0 2px, transparent 2px 4px)", pointerEvents: "none", opacity: 0.5 }} />
          </div>
        </AbsoluteFill>
      );
    }
    case "split": {
      const extra = spec.extras?.[0];
      if (!extra) return <KenBurns src={src} f={f} frame={frame} />;
      const x = 50 + Math.sin(seg(pp, 0.05, 0.95) * Math.PI) * 18;
      return (
        <AbsoluteFill>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f }} />
          <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${x}%)` }}>
            <Img src={staticFile(extra)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f }} />
          </AbsoluteFill>
          <div style={{ position: "absolute", left: `${x}%`, top: 0, width: 4, height: "100%", background: "#fff", boxShadow: "0 0 14px rgba(0,0,0,0.6)" }} />
        </AbsoluteFill>
      );
    }
    case "grid": {
      const imgs = [rel, ...(spec.extras || [])].slice(0, 4);
      if (imgs.length < 3) return <KenBurns src={src} f={f} frame={frame} />;
      while (imgs.length < 4) imgs.push(imgs[imgs.length - 1]);
      return (
        <AbsoluteFill style={{ background: "#0b1020", display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: 8, padding: 8 }}>
          {imgs.map((im, i) => {
            const s2 = spring({ frame: frame - i * 6, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 16 });
            return <div key={i} style={{ overflow: "hidden", opacity: s2, transform: `scale(${0.8 + s2 * 0.2})` }}>
              <Img src={staticFile(im)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: f }} />
            </div>;
          })}
        </AbsoluteFill>
      );
    }
    default:
      return <KenBurns src={src} f={f} frame={frame} />;
  }
};
