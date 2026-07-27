import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Loop,
  OffthreadVideo,
  Sequence,
  staticFile,
  interpolate,
  spring,
  random,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { MapAnimation } from "./MapAnimation";
import { SatelliteZoom } from "./SatelliteZoom";
import { Illustration, IlustracaoSpec, Safe } from "./Illustration";
import { Mascot } from "./Mascot";
import { YtCta } from "./YtCta";
import { Presentacao, PresentacaoSpec } from "./Presentacao";
import { KaraokeCaption } from "./KaraokeCaption";
import { ArchiveClip } from "./ArchiveClip";
import { PersonCard } from "./PersonCard";
import { MoodOverlay, moodVideoFilter, TVStatic, PeriodOverlay } from "./Effects";
import { ImageCard } from "./ImageCard";
import { ProductCTA } from "./ProductCTA";

type Info = { tipo: string; valor: number; sufixo: string; label: string };

type MapaSeg = {
  inicio: number;
  dur: number;
  pais: string;
  coord: [number, number];
  legenda: string;
  imagem_rel?: string | null;
  tipo?: "estilizado" | "satelite" | null;
  niveis?: { rel: string; half: number }[] | null;  // pilha de tiles de satélite
};

type PessoaSeg = {
  inicio: number;
  dur: number;
  nome: string;
  subtitulo?: string | null;
  imagem_rel?: string | null;
  fundo?: "claro" | "escuro";
};

type Cena = {
  inicio: number;
  fim: number;
  clip_rel: string;
  clip_dur: number;
  media_tipo?: "video" | "imagem";
  transicao?: string;
  texto_impacto?: string | null;
  palavra_chave?: string | null;
  texto_pos?: "left" | "center" | "right" | null;
  infografico?: Info | null;
  presentacao?: PresentacaoSpec | null;  // template de apresentação da imagem (lupa/spotlight/etc)
  sfx?: boolean;
  aparece_em?: number | null;
  fade?: number;
  entrada_texto?: string | null;
  intro?: boolean;
  ilustracao?: IlustracaoSpec | null;
  mascote?: { img_rel?: string; lado?: "left" | "right"; pose?: string } | null;
  personagens?: { img_rel: string; lado: "left" | "right" }[] | null;
  fonte?: string | null;            // "archive" => footage de arquivo
  arquivo_modo?: "fundir" | "enquadrar" | null;
  era?: string | null;
  mood?: string | null;             // tenso|frio|nostalgia|revelacao|misterioso|neutro
};
type Envelope = { step: number; vols: number[] };
type Timeline = {
  duracao: number;
  narracao_rel: string;
  musica_rel?: string | null;
  musica_envelope?: Envelope | null;
  click_rel?: string | null;
  cenas: Cena[];
  mapas?: MapaSeg[];
  pessoas?: PessoaSeg[];
  datas?: { inicio: number; texto: string; dur?: number }[];
  glitch_rel?: string | null;
  imagens?: { inicio: number; dur: number; estilo: "photo" | "split" | "clipping"; imagens_rel: string[]; legenda?: string | null }[];
  topicos?: { inicio: number; fim: number; titulo: string; mood: string }[];
  musica_segmentos?: { inicio: number; fim: number; vol: number; fade: number; track_rel: string }[];
  periodo?: string | null;   // "vintage" => doc de época: B&W + grão + vinheta
  fonte_tema?: string | null; // niche -> tema de fonte: serif|impact|typewriter|clean
  sfx_typing_rel?: string | null; // SFX de digitação (ASMR, vol baixo)
  sfx_paper_rel?: string | null;  // SFX de virar página (cards/imagens, vol baixo)
  sfx_whoosh_rel?: string | null; // SFX whoosh nas transições de movimento (whip/slide)
  sfx_riser_rel?: string | null;  // SFX riser subindo na fronteira de tópico
  cta_ding_rel?: string | null;   // SFX ding do sino no CTA
  ctas?: { inicio: number; dur: number; headline?: string }[] | null; // CTAs de YouTube (like/sub/bell)
  sfx_roles?: { transicao?: string[]; entrada?: string[]; first?: string; glitch?: string[] } | null; // SFX por papel (preset do nicho)
  glitch_topico?: boolean;
  ambiencias?: { inicio: number; fim: number; file_rel: string; gain_db?: number }[];
  foleys?: { t: number; file_rel: string; gain_db?: number }[];   // false (documentário) => sem TVStatic+som de glitch na fronteira de tópico
  produto_cta?: { inicio: number; fim: number; img?: string; qr?: string; headline?: string; offer?: string } | null;  // CTA de produto (takeover)
  legendas_hook?: { word: string; start: number; end: number }[] | null; // legenda hipnótica (palavras do whisper)
  hook_ate?: number | null;  // segundos de zona de hook (legenda dinâmica até aqui)
};

const FADE = 14; // ~0.47s de transição (cai no silêncio)
const ACCENT = "#facc15"; // cor de destaque da palavra-chave

// ---- Temas de fonte por NICHE (Director escolhe em fonte_tema) ----
type FontTheme = { head: string; ui: string; date: string; typing: boolean; upper: boolean };
const FONT_THEMES: Record<string, FontTheme> = {
  serif:      { head: "Georgia,'Times New Roman',serif", ui: "'Segoe UI',system-ui,sans-serif", date: "Georgia,'Times New Roman',serif", typing: false, upper: false },
  impact:     { head: "'Impact','Haettenschweiler','Arial Narrow',sans-serif", ui: "'Arial','Segoe UI',sans-serif", date: "'Impact','Arial Black',sans-serif", typing: false, upper: true },
  typewriter: { head: "'Courier New',Consolas,monospace", ui: "'Courier New',Consolas,monospace", date: "'Courier New',Consolas,monospace", typing: true, upper: false },
  clean:      { head: "'Segoe UI',system-ui,sans-serif", ui: "'Segoe UI',system-ui,sans-serif", date: "'Segoe UI',system-ui,sans-serif", typing: false, upper: false },
};
const themeOf = (k?: string | null): FontTheme => FONT_THEMES[k || "serif"] || FONT_THEMES.serif;

// Intensidades do tratamento (0 = off, 1 = forte) — calibre aqui
const GRADE = 0.6;   // grade de cor duotone cósmico (unifica os clips)
const VIG = 0.7;     // vinheta
const GRAIN_OP = 0.07; // film grain

// Animação de ENTRADA da cena conforme o tipo de transição (roda nos 1ºs FADE frames)
const entrada = (transicao: string, p: number) => {
  // p: 0 -> 1 durante a transição
  switch (transicao) {
    case "slide_left": // entra da direita
      return { opacity: 1, transform: `translateX(${(1 - p) * 100}%)`, filter: "none" };
    case "slide_right": // entra da esquerda
      return { opacity: 1, transform: `translateX(${-(1 - p) * 100}%)`, filter: "none" };
    case "zoom":
      return { opacity: p, transform: `scale(${1 + (1 - p) * 0.18})`, filter: "none" };
    case "whip":
      return { opacity: Math.min(1, p * 1.6), transform: `translateX(${(1 - p) * 55}%)`, filter: `blur(${(1 - p) * 22}px)` };
    case "crossfade":
    default:
      return { opacity: p, transform: "none", filter: "none" };
  }
};

const DESTOCK = true; // "amadoriza" o stock de vídeo (handheld drift + degradê). Toggle p/ comparar.

const SceneClip: React.FC<{ rel: string; transicao: string; isFirst: boolean; clipDurFrames: number; fadeFrames?: number; vfilter?: string; mediaTipo?: "video" | "imagem"; presentacao?: PresentacaoSpec | null; sceneFrames?: number }> = ({ rel, transicao, isFirst, clipDurFrames, fadeFrames = FADE, vfilter = "none", mediaTipo = "video", presentacao = null, sceneFrames = 150 }) => {
  const frame = useCurrentFrame();
  const p = isFirst ? 1 : interpolate(frame, [0, fadeFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const st = isFirst ? { opacity: 1, transform: "none", filter: "none" } : entrada(transicao, p);
  // imagem -> Ken Burns lento; vídeo -> OffthreadVideo em loop
  const kb = 1.0 + 0.12 * Math.min(1, frame / 300);
  // DESTOCK: dá cara de "handheld/amador" ao stock de vídeo — micro-drift por seno + leve degradê de cor.
  // scale(1.07) esconde a borda do translate/rotate. Imagens NÃO recebem (já têm Ken Burns).
  const t = frame / 30;
  const hx = (Math.sin(t * 1.3) * 6 + Math.sin(t * 0.47) * 3.5);
  const hy = (Math.cos(t * 1.07) * 4.5 + Math.sin(t * 0.7) * 2.5);
  const hr = Math.sin(t * 0.6) * 0.35;
  const vidFilter = DESTOCK ? `${vfilter === "none" ? "" : vfilter} contrast(1.05) saturate(0.9)`.trim() : vfilter;
  const vidTransform = DESTOCK ? `scale(1.07) translate(${hx.toFixed(2)}px, ${hy.toFixed(2)}px) rotate(${hr.toFixed(3)}deg)` : "none";
  return (
    <AbsoluteFill style={{ opacity: st.opacity, transform: st.transform, filter: st.filter }}>
      {mediaTipo === "imagem" ? (
        presentacao && presentacao.tipo && presentacao.tipo !== "kenburns" ? (
          <Safe><Presentacao spec={presentacao} rel={rel} sceneFrames={sceneFrames} vfilter={vfilter} /></Safe>
        ) : (
          <Img src={staticFile(rel)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: vfilter, transform: `scale(${kb.toFixed(4)})` }} />
        )
      ) : (
        <Loop durationInFrames={Math.max(1, clipDurFrames)}>
          <OffthreadVideo src={staticFile(rel)} muted style={{ width: "100%", height: "100%", objectFit: "cover", filter: vidFilter, transform: vidTransform }} />
        </Loop>
      )}
    </AbsoluteFill>
  );
};

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/gi, "");

const KineticText: React.FC<{ texto: string; palavra?: string | null; pos: string; sceneFrames: number; entrada?: string; fonts?: FontTheme }> = ({ texto, palavra, pos, sceneFrames, entrada = "words", fonts = FONT_THEMES.serif }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = texto.split(" ");
  const kw = palavra ? norm(palavra) : "";
  const fadeOut = interpolate(frame, [sceneFrames - 12, sceneFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const align = pos === "left" ? "flex-start" : pos === "right" ? "flex-end" : "center";
  const padSide = pos === "center" ? "0 60px" : "0 90px";

  // TYPEWRITER — revela caractere a caractere + cursor piscando (tema typewriter)
  if (fonts.typing) {
    const cps = 24;
    const nshow = Math.min(texto.length, Math.max(0, Math.floor((frame / fps) * cps)));
    const done = nshow >= texto.length;
    const cursorOn = Math.floor(frame / 8) % 2 === 0;
    return (
      <AbsoluteFill style={{ justifyContent: "center", alignItems: align, opacity: fadeOut, padding: padSide }}>
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0.5) 0%, transparent 62%)" }} />
        <div style={{
          fontFamily: fonts.head, fontSize: 60, fontWeight: 700, color: "#fff", maxWidth: "78%",
          textAlign: pos === "right" ? "right" : pos === "left" ? "left" : "center",
          letterSpacing: 1, lineHeight: 1.35, textShadow: "0 2px 22px rgba(0,0,0,0.95)",
        }}>
          {texto.slice(0, nshow)}
          <span style={{ color: ACCENT, opacity: (!done || cursorOn) ? 1 : 0 }}>▋</span>
        </div>
      </AbsoluteFill>
    );
  }

  const perWord = entrada === "words" || entrada === "cascade";
  // entrada do BLOCO inteiro (pop / blur / up / slam)
  const tb = spring({ frame, fps, config: { damping: 14, stiffness: 130, mass: 0.5 }, durationInFrames: 16 });
  const tbSlam = spring({ frame, fps, config: { damping: 9, stiffness: 200, mass: 0.6 }, durationInFrames: 14 });
  let blockStyle: React.CSSProperties = {};
  if (entrada === "pop") blockStyle = { transform: `scale(${0.55 + tb * 0.45})`, opacity: tb };
  else if (entrada === "blur") blockStyle = { filter: `blur(${(1 - tb) * 24}px)`, opacity: tb };
  else if (entrada === "up") blockStyle = { transform: `translateY(${(1 - tb) * 70}px)`, opacity: tb };
  else if (entrada === "slam") blockStyle = { transform: `scale(${1 + (1 - tbSlam) * 0.6})`, opacity: Math.min(1, tb * 1.6) };

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: align, opacity: fadeOut }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0.42) 0%, transparent 62%)" }} />
      <div style={{
        display: "flex", flexWrap: "wrap",
        justifyContent: align,
        textAlign: pos === "right" ? "right" : pos === "left" ? "left" : "center",
        maxWidth: "70%", padding: padSide,
        ...(!perWord ? blockStyle : {}),
      }}>
        {words.map((w, i) => {
          // cascade = pop por palavra rápido (mais kinético); words = sobe por palavra
          const stagger = entrada === "cascade" ? 3 : 4;
          const tw = spring({ frame: frame - i * stagger, fps, config: { damping: entrada === "cascade" ? 11 : 14, stiffness: entrada === "cascade" ? 170 : 120, mass: 0.5 }, durationInFrames: entrada === "cascade" ? 14 : 18 });
          let wAnim: React.CSSProperties = {};
          if (entrada === "words") wAnim = { opacity: tw, transform: `translateY(${(1 - tw) * 26}px)` };
          else if (entrada === "cascade") wAnim = { opacity: Math.min(1, tw * 1.4), transform: `scale(${0.4 + tw * 0.6}) translateY(${(1 - tw) * 18}px)`, display: "inline-block" };
          const isKw = kw && norm(w) === kw;
          return (
            <span key={i} style={{
              fontFamily: fonts.head,
              fontSize: fonts.upper ? 92 : 80, fontWeight: fonts.upper ? 900 : 700,
              textTransform: fonts.upper ? "uppercase" : "none",
              color: isKw ? ACCENT : "#ffffff",
              textShadow: isKw
                ? `0 2px 26px rgba(0,0,0,0.95), 0 0 50px ${ACCENT}66`
                : "0 2px 26px rgba(0,0,0,0.95), 0 0 55px rgba(0,0,0,0.6)",
              letterSpacing: fonts.upper ? 1.5 : 0.5, lineHeight: 1.2, marginRight: "0.28em",
              ...wAnim,
            }}>{w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const LABEL_STYLE: React.CSSProperties = {
  marginTop: 14, fontSize: 30, color: "#e8e8e8", textTransform: "uppercase",
  letterSpacing: 3, fontWeight: 600, fontFamily: "'Segoe UI', system-ui, sans-serif",
  textShadow: "0 2px 20px rgba(0,0,0,0.92)",
};

const InfoGraphic: React.FC<{ info: Info; pos: string; sceneFrames: number }> = ({ info, pos, sceneFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const countDur = Math.round(1.1 * fps);
  const p = interpolate(frame, [4, 4 + countDur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const valorN = typeof info.valor === "number" && Number.isFinite(info.valor)
    ? info.valor : (parseFloat(String(info.valor).replace(/[^0-9.\-]/g, "")) || 0);
  const val = valorN * p;
  const dec = Number.isInteger(valorN) ? 0 : 1;
  const fadeOut = interpolate(frame, [sceneFrames - 12, sceneFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const appear = spring({ frame, fps, config: { damping: 16, stiffness: 110 }, durationInFrames: 18 });
  const align = pos === "left" ? "flex-start" : pos === "right" ? "flex-end" : "center";
  const padSide = pos === "center" ? "0" : "0 110px";
  const numStyle: React.CSSProperties = {
    fontFamily: "'Segoe UI', system-ui, sans-serif", fontWeight: 800, color: "#ffffff",
    textShadow: `0 2px 30px rgba(0,0,0,0.9), 0 0 55px ${ACCENT}55`, lineHeight: 1,
  };

  if (info.tipo === "ring") {
    const R = 120, SW = 14, C = 2 * Math.PI * R;
    const off = C * (1 - val / 100);
    return (
      <AbsoluteFill style={{ justifyContent: "center", alignItems: align, opacity: fadeOut, padding: padSide }}>
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0.5) 0%, transparent 62%)" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${0.85 + appear * 0.15})`, opacity: appear }}>
          <div style={{ position: "relative", width: 280, height: 280 }}>
            <svg width="280" height="280">
              <circle cx="140" cy="140" r={R} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={SW} />
              <circle cx="140" cy="140" r={R} fill="none" stroke={ACCENT} strokeWidth={SW} strokeLinecap="round"
                strokeDasharray={C} strokeDashoffset={off} transform="rotate(-90 140 140)" />
            </svg>
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ ...numStyle, fontSize: 84 }}>{val.toFixed(dec)}{info.sufixo}</span>
            </div>
          </div>
          <span style={LABEL_STYLE}>{info.label}</span>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: align, opacity: fadeOut, padding: padSide }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0.5) 0%, transparent 62%)" }} />
      <div style={{ display: "flex", flexDirection: "column", alignItems: align, transform: `translateY(${(1 - appear) * 24}px)`, opacity: appear }}>
        <span style={{ ...numStyle, fontSize: 150 }}>
          {val.toFixed(dec)}<span style={{ fontSize: 62, color: ACCENT }}>{info.sufixo}</span>
        </span>
        <span style={LABEL_STYLE}>{info.label}</span>
      </div>
    </AbsoluteFill>
  );
};

// Neve caindo (screen, sutil)
const SNOW_N = 70;
const Snow: React.FC = () => {
  const frame = useCurrentFrame(); const { width, height, fps } = useVideoConfig(); const t = frame / fps;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none", opacity: 0.5 }}>
      {Array.from({ length: SNOW_N }).map((_, i) => {
        const sx = random(`snx${i}`), sp = random(`sns${i}`) * 0.5 + 0.3, sz = random(`snz${i}`) * 4 + 1.5;
        const sway = random(`snw${i}`) * 60 - 30;
        const x = sx * width + Math.sin(t * 0.6 + i) * sway;
        const y = ((t * sp * 120) + i * 53) % (height + 60);
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: sz, height: sz, borderRadius: "50%", background: "#fff", opacity: random(`sno${i}`) * 0.5 + 0.3, filter: "blur(0.5px)" }} />;
      })}
    </AbsoluteFill>
  );
};

// Névoa drift (screen, bem sutil)
const Fog: React.FC = () => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig(); const t = frame / fps;
  const x = Math.sin(t * 0.1) * 10;
  return <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none", opacity: 0.1,
    background: `radial-gradient(ellipse at ${40 + x}% 82%, rgba(180,190,210,0.5) 0%, transparent 55%)` }} />;
};

// God rays — raios divinos do topo, pulsando
const GodRays: React.FC = () => {
  const frame = useCurrentFrame(); const { width, height, fps } = useVideoConfig(); const t = frame / fps;
  const rays = [-22, -10, 2, 14, 26];
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none" }}>
      <svg width={width} height={height}>
        <defs><linearGradient id="godray" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(255,236,170,0.28)" /><stop offset="100%" stopColor="rgba(255,236,170,0)" />
        </linearGradient></defs>
        {rays.map((a, i) => {
          const breath = 0.35 + 0.3 * Math.sin(t * 0.8 + i * 0.5);
          return <polygon key={i} points={`${width * 0.5 - 60},0 ${width * 0.5 + 60},0 ${width * 0.5 + 420},${height * 1.2} ${width * 0.5 - 420},${height * 1.2}`}
            fill="url(#godray)" opacity={breath} transform={`rotate(${a} ${width * 0.5} -40)`} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

// Light streaks anamórficas drift (screen)
const LightStreaks: React.FC = () => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig(); const t = frame / fps;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none" }}>
      {[0, 1, 2].map((i) => {
        const y = 18 + i * 30, op = 0.06 + 0.05 * Math.sin(t * 0.5 + i * 2);
        const x = ((t * 8 + i * 45) % 150) - 25;
        return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: "55%", height: 3,
          background: `linear-gradient(90deg, transparent, rgba(150,200,255,${op}), transparent)`, filter: "blur(2px)" }} />;
      })}
    </AbsoluteFill>
  );
};

// Música com DUCKING dinâmico (envelope: baixa na fala, sobe nas pausas) + fade in/out
const Musica: React.FC<{ rel: string; env?: Envelope | null; totalFrames: number }> = ({ rel, env, totalFrames }) => {
  const { fps } = useVideoConfig();
  const fin = Math.round(2 * fps);
  const fout = Math.round(3 * fps);
  return (
    <Audio
      src={staticFile(rel)}
      volume={(f) => {
        let v = 0.18;
        if (env && env.vols.length) {
          const idx = Math.min(env.vols.length - 1, Math.max(0, Math.round((f / fps) / env.step)));
          v = env.vols[idx];
        }
        const fade = interpolate(f, [0, fin, totalFrames - fout, totalFrames], [0, 1, 1, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        return v * fade;
      }}
    />
  );
};

// Film grain — textura PRÉ-ASSADA (grain.png) animada por background-position.
// Evita feTurbulence em runtime (recomputar ruído fractal por frame era o maior custo do render).
const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const x = (frame * 41) % 640;
  const y = (frame * 27) % 640;
  return (
    <AbsoluteFill style={{
      mixBlendMode: "overlay", opacity: GRAIN_OP, pointerEvents: "none",
      backgroundImage: `url(${staticFile("grain.png")})`,
      backgroundRepeat: "repeat", backgroundSize: "640px 640px",
      backgroundPosition: `${x}px ${y}px`,
    }} />
  );
};

// Grade de cor DUOTONE cósmico — unifica os clips de stock numa paleta só.
// Sombras cool (teal/navy via multiply) + highlights roxos (screen) + coesão (soft-light).
const ColorGrade: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ mixBlendMode: "multiply", opacity: 0.4 * GRADE,
      background: "linear-gradient(180deg, #1a2747 0%, #0f1d2e 100%)" }} />
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.16 * GRADE,
      background: "radial-gradient(circle at 50% 38%, #5a3a8f 0%, #160e2e 72%)" }} />
    <AbsoluteFill style={{ mixBlendMode: "soft-light", opacity: 0.45 * GRADE,
      background: "#6e54b0" }} />
  </AbsoluteFill>
);

// Vinheta — escurece bordas pra foco/profundidade
const Vignette: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none",
    background: `radial-gradient(ellipse at center, transparent 56%, rgba(0,0,0,${0.62 * VIG}) 100%)` }} />
);

// Partículas de poeira cósmica subindo (drift aleatório, screen)
const PART_N = 60;
const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none", opacity: 0.55 }}>
      {Array.from({ length: PART_N }).map((_, i) => {
        const sx = random(`px${i}`);
        const speed = random(`ps${i}`) * 0.4 + 0.2;
        const size = random(`pz${i}`) * 3.2 + 1;
        const op = random(`po${i}`) * 0.5 + 0.25;
        const drift = random(`pd${i}`) * 40 - 20;
        const x = sx * width + Math.sin(t * 0.4 + i) * drift;
        const yProg = ((t * speed * 90) + i * 61) % (height + 80);
        const y = height - yProg;
        const col = random(`pc${i}`) > 0.5 ? "#fff7e0" : ACCENT;
        return (
          <div key={i} style={{
            position: "absolute", left: x, top: y, width: size, height: size,
            borderRadius: "50%", background: col, opacity: op,
            boxShadow: `0 0 ${size * 3}px ${col}`,
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

// Bokeh — esferas grandes desfocadas drift lento (profundidade)
const BOKEH_N = 7;
const Bokeh: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", pointerEvents: "none", filter: "blur(2px)" }}>
      {Array.from({ length: BOKEH_N }).map((_, i) => {
        const sx = random(`bx${i}`), sy = random(`by${i}`);
        const size = random(`bz${i}`) * 130 + 60;
        const x = sx * width + Math.sin(t * 0.15 + i * 1.3) * 60;
        const y = sy * height + Math.cos(t * 0.12 + i) * 40;
        const op = 0.10 + 0.08 * Math.sin(t * 0.5 + i);
        return (
          <div key={i} style={{
            position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%",
            background: `radial-gradient(circle, rgba(255,222,150,${Math.max(0, op)}) 0%, transparent 70%)`,
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

// Light leak quente, drift + pulso suave (mix screen)
const LightLeak: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const x = 82 + Math.sin(t * 0.3) * 12;
  const op = 0.05 + 0.06 * Math.max(0, Math.sin(t * 0.45));
  return (
    <AbsoluteFill style={{
      mixBlendMode: "screen", pointerEvents: "none",
      background: `radial-gradient(circle at ${x}% 16%, rgba(255,184,92,${op}) 0%, transparent 46%)`,
    }} />
  );
};

// Pool de atmosferas que VARIAM e EMPILHAM por vídeo (random seeded — troque STACK_SEED p/ variar)
const STACK_SEED = "v1";
const ATMOS: { k: string; C: React.FC }[] = [
  { k: "bokeh", C: Bokeh }, { k: "particles", C: Particles }, { k: "lightleak", C: LightLeak },
  { k: "godrays", C: GodRays }, { k: "streaks", C: LightStreaks }, { k: "fog", C: Fog }, { k: "snow", C: Snow },
];
const pickAtmos = (n: number) =>
  ATMOS.map((a) => ({ a, r: random(`${STACK_SEED}-${a.k}`) }))
    .sort((x, y) => x.r - y.r).slice(0, n).map((s) => s.a);

// Mapa que toma a tela com fade in/out (cobre o B-roll no momento do lugar citado)
const MapFade: React.FC<{ m: MapaSeg; durFrames: number }> = ({ m, durFrames }) => {
  const f = useCurrentFrame();
  const fadeF = 10;
  const op = interpolate(f, [0, fadeF, durFrames - fadeF, durFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const sat = m.tipo === "satelite" && m.niveis && m.niveis.length >= 2;
  return (
    <AbsoluteFill style={{ opacity: op }}>
      {sat ? (
        <SatelliteZoom durFrames={durFrames} niveis={m.niveis!} coord={m.coord} legenda={m.legenda} />
      ) : (
        <MapAnimation durFrames={durFrames} pais={m.pais} coord={m.coord} legenda={m.legenda}
          imagem_rel={m.imagem_rel || "test/map_img.jpg"} />
      )}
    </AbsoluteFill>
  );
};

// Imagem PD do caso (toma a tela com fade in/out; estilos photo/split/clipping)
const ImageFade: React.FC<{ im: { estilo: "photo" | "split" | "clipping"; imagens_rel: string[]; legenda?: string | null }; durFrames: number; fonts?: FontTheme }> = ({ im, durFrames, fonts = FONT_THEMES.serif }) => {
  const f = useCurrentFrame();
  const fadeF = 9;
  const op = interpolate(f, [0, fadeF, durFrames - fadeF, durFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <ImageCard estilo={im.estilo} imagens={im.imagens_rel} legenda={im.legenda} durFrames={durFrames} capFont={fonts.ui} />
    </AbsoluteFill>
  );
};

// Card de pessoa histórica que toma a tela com fade in/out
const PersonFade: React.FC<{ p: PessoaSeg; durFrames: number; fonts?: FontTheme }> = ({ p, durFrames, fonts = FONT_THEMES.serif }) => {
  const f = useCurrentFrame();
  const fadeF = 9;
  const op = interpolate(f, [0, fadeF, durFrames - fadeF, durFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <PersonCard nome={p.nome} imagem_rel={p.imagem_rel || "test/people/darwin.png"}
        subtitulo={p.subtitulo} fundo={p.fundo || "escuro"} durFrames={durFrames}
        headFont={fonts.head} uiFont={fonts.ui} />
    </AbsoluteFill>
  );
};

// Clipe de arquivo com crossfade de entrada (usa ArchiveClip: fundir|enquadrar)
const ArchiveFade: React.FC<{ rel: string; modo: "fundir" | "enquadrar"; era: string; durFrames: number; fadeFrames: number }> = ({ rel, modo, era, durFrames, fadeFrames }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, fadeFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <ArchiveClip rel={rel} modo={modo} era={era} durFrames={durFrames} />
    </AbsoluteFill>
  );
};

// Data em fonte grande (slam-in), sincronizada à fala
const DateStamp: React.FC<{ texto: string; durFrames: number; fonts?: FontTheme }> = ({ texto, durFrames, fonts = FONT_THEMES.serif }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inS = spring({ frame: f, fps, config: { damping: 12 }, durationInFrames: 14 });
  const out = interpolate(f, [durFrames - 10, durFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = Math.min(inS, out);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 160, opacity: op }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center bottom, rgba(0,0,0,0.45) 0%, transparent 55%)", pointerEvents: "none" }} />
      <div style={{ position: "relative", transform: `scale(${0.7 + 0.3 * inS})` }}>
        <div style={{ fontFamily: fonts.date, fontWeight: 900, fontSize: 112, color: "#fff",
          letterSpacing: 3, textShadow: "0 6px 26px rgba(0,0,0,0.85)", textTransform: "uppercase", lineHeight: 1 }}>{texto}</div>
        <div style={{ height: 5, background: ACCENT, width: `${Math.round(inS * 100)}%`, margin: "10px auto 0", borderRadius: 3 }} />
      </div>
    </AbsoluteFill>
  );
};

export const BrollTest: React.FC<{ timeline: Timeline | null }> = ({ timeline }) => {
  const { fps } = useVideoConfig();
  if (!timeline) return null;
  const n = timeline.cenas.length;
  const totalFrames = Math.ceil(timeline.duracao * fps);
  const bw = timeline.periodo === "vintage";
  const theme = themeOf(timeline.fonte_tema);
  const periodFilter = bw ? "grayscale(0.9) sepia(0.18) contrast(1.12) brightness(1.03)" : "";
  const vfilterDe = (mood?: string | null) =>
    [moodVideoFilter(mood), periodFilter].filter((s) => s && s !== "none").join(" ") || "none";
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* CAMADA 1 — B-roll + transições + click SFX */}
      {timeline.cenas.map((c, i) => {
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        const myFade = c.fade ?? FADE;
        const nextFade = i < n - 1 ? (timeline.cenas[i + 1].fade ?? FADE) : 0;
        const dur = sceneFrames + nextFade;
        const clipDurFrames = Math.floor((c.clip_dur || 5) * fps);
        const isArchive = c.fonte === "archive";
        return (
          <Sequence key={`clip-${i}`} from={start} durationInFrames={dur}>
            {isArchive ? (
              <ArchiveFade rel={c.clip_rel} modo={c.arquivo_modo || "fundir"} era={c.era || "ARCHIVE"} durFrames={dur} fadeFrames={myFade} />
            ) : (
              <SceneClip rel={c.clip_rel} transicao={c.transicao || "crossfade"} isFirst={i === 0} clipDurFrames={clipDurFrames} fadeFrames={myFade} vfilter={vfilterDe(c.mood)} mediaTipo={c.media_tipo} presentacao={c.presentacao} sceneFrames={sceneFrames} />
            )}
          </Sequence>
        );
      })}

      {/* CAMADA 1.5 — Mapas: tomam a tela no momento do lugar citado (fade in/out). Ficam ABAIXO do tratamento p/ herdar grade+grão+vinheta e unificar com o vídeo */}
      {(timeline.mapas || []).map((m, i) => {
        const start = Math.floor(m.inicio * fps);
        const durFrames = Math.ceil(m.dur * fps);
        return (
          <Sequence key={`map-${i}`} from={start} durationInFrames={durFrames}>
            <MapFade m={m} durFrames={durFrames} />
          </Sequence>
        );
      })}

      {/* CAMADA 2 — Tratamento base (coesão): grade + vinheta (+ época P&B/grão se doc histórico) */}
      <ColorGrade />
      <Vignette />
      {bw ? <PeriodOverlay /> : null}

      {/* CAMADA 2.5 — EFEITOS POR CONTEXTO (humor): wash de cor / CRT-VHS / static / glitch, por cena */}
      {timeline.cenas.map((c, i) => {
        if (!c.mood || c.mood === "neutro") return null;
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        const nextFade = i < n - 1 ? (timeline.cenas[i + 1].fade ?? FADE) : 0;
        return (
          <Sequence key={`fx-${i}`} from={start} durationInFrames={sceneFrames + nextFade}>
            <MoodOverlay mood={c.mood} bw={bw} />
          </Sequence>
        );
      })}

      {/* CAMADA 2.6 — Glitch/static SÓ na fronteira de TÓPICO (não em mudança de humor).
          Desligado quando glitch_topico===false (documentário: estática digital é anacrônica). */}
      {timeline.glitch_topico !== false && (timeline.topicos || []).map((t, i) => {
        if (i === 0) return null; // não no começo do vídeo
        const start = Math.floor(t.inicio * fps);
        const durFrames = Math.round(0.5 * fps);
        return (
          <Sequence key={`topfx-${i}`} from={start} durationInFrames={durFrames}>
            <TVStatic durFrames={durFrames} />
            {(timeline.sfx_roles?.glitch?.length || timeline.glitch_rel)
              ? <Audio src={staticFile(timeline.sfx_roles?.glitch?.length ? timeline.sfx_roles.glitch[i % timeline.sfx_roles.glitch.length] : timeline.glitch_rel!)} volume={0.45} />
              : null}
          </Sequence>
        );
      })}

      <Grain />

      {/* CAMADA 3a — Ilustrações (ícone/gráfico/card) no topo, sincronizadas à fala */}
      {timeline.cenas.map((c, i) => {
        if (!c.ilustracao) return null;
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        const nextFade = i < n - 1 ? (timeline.cenas[i + 1].fade ?? FADE) : 0;
        const dur = sceneFrames + nextFade;
        const apareceEm = c.aparece_em != null ? c.aparece_em : c.inicio;
        const delay = Math.max(0, Math.round((apareceEm - c.inicio) * fps));
        const ovFrames = Math.max(20, sceneFrames - delay);
        return (
          <Sequence key={`ilu-${i}`} from={start} durationInFrames={dur}>
            <Sequence from={delay} durationInFrames={ovFrames}>
              <Illustration spec={c.ilustracao} sceneFrames={ovFrames} />
            </Sequence>
          </Sequence>
        );
      })}

      {/* CAMADA 3b — MASCOTE (personagem do canal, pass mascote.py): pop de mola a cada 2-3 cenas */}
      {timeline.cenas.map((c, i) => {
        if (!c.mascote || !c.mascote.img_rel) return null;
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        return (
          <Sequence key={`masc-${i}`} from={start} durationInFrames={sceneFrames}>
            <Mascot imgRel={c.mascote.img_rel} lado={c.mascote.lado === "left" ? "left" : "right"} sceneFrames={sceneFrames} />
          </Sequence>
        );
      })}

      {/* CAMADA 3c — PERSONAGENS DA HISTÓRIA (story engine): elenco recortado nas laterais, por presença na cena */}
      {timeline.cenas.map((c, i) => {
        if (!c.personagens || !c.personagens.length) return null;
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        return (
          <Sequence key={`pers-${i}`} from={start} durationInFrames={sceneFrames}>
            {c.personagens.map((p, k) => (
              <Mascot key={k} imgRel={p.img_rel} lado={p.lado} sceneFrames={sceneFrames} alturaFrac={0.5} />
            ))}
          </Sequence>
        );
      })}

      {/* CAMADA SOM-A — AMBIÊNCIAS ASMR (story engine): loops por janela de cena, fade nas bordas */}
      {(timeline.ambiencias || []).map((a, i) => {
        const from = Math.floor(a.inicio * fps);
        const dur = Math.max(fps, Math.round((a.fim - a.inicio) * fps));
        const vol = Math.pow(10, (a.gain_db ?? -6) / 20);
        return (
          <Sequence key={`amb-${i}`} from={from} durationInFrames={dur}>
            <Audio src={staticFile(a.file_rel)} loop volume={(f) =>
              vol * Math.min(1, f / (fps * 1.2), Math.max(0.0001, (dur - f) / (fps * 1.2)))} />
          </Sequence>
        );
      })}

      {/* CAMADA SOM-B — FOLEY (story engine): one-shots ancorados na palavra falada */}
      {(timeline.foleys || []).map((fl, i) => {
        const from = Math.floor(fl.t * fps);
        const vol = Math.pow(10, (fl.gain_db ?? -6) / 20);
        return (
          <Sequence key={`fol-${i}`} from={from} durationInFrames={fps * 5}>
            <Audio src={staticFile(fl.file_rel)} volume={vol} />
          </Sequence>
        );
      })}

      {/* CAMADA 3 — Texto / infográficos no topo (nítidos, sem grade/grão por cima) */}
      {timeline.cenas.map((c, i) => {
        if (!c.infografico && !c.texto_impacto) return null;
        const start = Math.floor(c.inicio * fps);
        const sceneFrames = Math.ceil((c.fim - c.inicio) * fps);
        const nextFade = i < n - 1 ? (timeline.cenas[i + 1].fade ?? FADE) : 0;
        const dur = sceneFrames + nextFade;
        const apareceEm = c.aparece_em != null ? c.aparece_em : c.inicio;
        const delay = Math.max(0, Math.round((apareceEm - c.inicio) * fps));
        const ovFrames = Math.max(15, sceneFrames - delay);
        const overlay = c.infografico ? (
          <InfoGraphic info={c.infografico} pos={c.texto_pos || "center"} sceneFrames={ovFrames} />
        ) : (
          <KineticText texto={c.texto_impacto!} palavra={c.palavra_chave} pos={c.texto_pos || "center"} sceneFrames={ovFrames} entrada={c.entrada_texto || "words"} fonts={theme} />
        );
        return (
          <Sequence key={`txt-${i}`} from={start} durationInFrames={dur}>
            <Sequence from={delay} durationInFrames={ovFrames}><Safe>{overlay}</Safe></Sequence>
          </Sequence>
        );
      })}

      {/* CAMADA 3c — Datas em fonte grande, sincronizadas à fala */}
      {(timeline.datas || []).map((d, i) => {
        const start = Math.floor(d.inicio * fps);
        const durFrames = Math.ceil((d.dur || 2.6) * fps);
        return (
          <Sequence key={`data-${i}`} from={start} durationInFrames={durFrames}>
            <DateStamp texto={d.texto} durFrames={durFrames} fonts={theme} />
          </Sequence>
        );
      })}

      {/* CAMADA 3d — Imagens PD do caso (tomam a tela; photo/split/clipping) */}
      {(timeline.imagens || []).map((im, i) => {
        const start = Math.floor(im.inicio * fps);
        const durFrames = Math.ceil(im.dur * fps);
        return (
          <Sequence key={`img-${i}`} from={start} durationInFrames={durFrames}>
            <ImageFade im={im} durFrames={durFrames} fonts={theme} />
          </Sequence>
        );
      })}

      {/* CAMADA 4 — Cards de pessoa (tomam a tela no nome citado), topmost visual */}
      {(timeline.pessoas || []).map((p, i) => {
        const start = Math.floor(p.inicio * fps);
        const durFrames = Math.ceil(p.dur * fps);
        return (
          <Sequence key={`pes-${i}`} from={start} durationInFrames={durFrames}>
            <PersonFade p={p} durFrames={durFrames} fonts={theme} />
          </Sequence>
        );
      })}

      {/* CAMADA 4.5 — Legenda HIPNÓTICA na zona de hook (palavras sincronizadas, retém no começo) */}
      {timeline.legendas_hook && timeline.legendas_hook.length && timeline.hook_ate
        ? (
          <Sequence from={0} durationInFrames={Math.ceil((timeline.hook_ate || 0) * fps)}>
            <Safe><KaraokeCaption words={timeline.legendas_hook} fonts={theme} /></Safe>
          </Sequence>
        )
        : null}

      {/* CAMADA 5 — CTA de YouTube (like/subscribe/bell), topmost */}
      {(timeline.ctas || []).map((cta, i) => {
        const start = Math.floor(cta.inicio * fps);
        const durFrames = Math.ceil(cta.dur * fps);
        return (
          <Sequence key={`cta-${i}`} from={start} durationInFrames={durFrames}>
            <Safe><YtCta durFrames={durFrames} headline={cta.headline || undefined} /></Safe>
            {timeline.click_rel ? (
              <>
                <Sequence from={Math.round(0.7 * fps)} durationInFrames={Math.round(0.2 * fps)}><Audio src={staticFile(timeline.click_rel)} volume={0.7} /></Sequence>
                <Sequence from={Math.round(1.7 * fps)} durationInFrames={Math.round(0.2 * fps)}><Audio src={staticFile(timeline.click_rel)} volume={0.7} /></Sequence>
              </>
            ) : null}
            {timeline.cta_ding_rel ? (
              <Sequence from={Math.round(2.8 * fps)} durationInFrames={Math.round(1.0 * fps)}><Audio src={staticFile(timeline.cta_ding_rel)} volume={0.4} /></Sequence>
            ) : null}
          </Sequence>
        );
      })}

      {/* CAMADA 6 — CTA de PRODUTO (mockup eBook + QR), takeover sincronizado ao soft-sell falado (~8min) */}
      {timeline.produto_cta ? (
        <Sequence from={Math.floor(timeline.produto_cta.inicio * fps)} durationInFrames={Math.max(1, Math.round((timeline.produto_cta.fim - timeline.produto_cta.inicio) * fps))}>
          <Safe><ProductCTA productImg={timeline.produto_cta.img || undefined} qrImg={timeline.produto_cta.qr || undefined} headline={timeline.produto_cta.headline || undefined} offer={timeline.produto_cta.offer || undefined} /></Safe>
        </Sequence>
      ) : null}

      <Audio src={staticFile(timeline.narracao_rel)} volume={Number(timeline.__mute_narr) ? 0 : 1} />

      {/* CAMADA SFX ASMR — digitação no texto (só tema typewriter) + virar página em imagens/cards.
          Volume BAIXO (abaixo do glitch de transição 0.22), só pra dar textura. */}
      {theme.typing && timeline.sfx_typing_rel
        ? timeline.cenas.map((c, i) => {
            if (!c.texto_impacto) return null;
            const apareceEm = c.aparece_em != null ? c.aparece_em : c.inicio;
            const start = Math.floor(apareceEm * fps);
            const typeFrames = Math.min(Math.ceil(2.2 * fps), Math.ceil((c.texto_impacto.length / 24) * fps) + 4);
            return (
              <Sequence key={`sfxt-${i}`} from={start} durationInFrames={typeFrames}>
                <Audio src={staticFile(timeline.sfx_typing_rel)} volume={0.09} />
              </Sequence>
            );
          })
        : null}
      {timeline.sfx_paper_rel
        ? [
            ...(timeline.imagens || []).map((im) => im.inicio),
            ...(timeline.pessoas || []).map((p) => p.inicio),
          ].map((t, i) => (
            <Sequence key={`sfxp-${i}`} from={Math.floor(t * fps)} durationInFrames={Math.ceil(1.2 * fps)}>
              <Audio src={staticFile(timeline.sfx_paper_rel!)} volume={0.1} />
            </Sequence>
          ))
        : null}

      {/* CAMADA SFX — TRANSIÇÃO (click alternado) nos cortes de movimento (whip/slide) */}
      {(timeline.sfx_roles?.transicao?.length || timeline.click_rel)
        ? timeline.cenas.map((c, i) => {
            if (i === 0 || !["whip", "slide_left", "slide_right"].includes(c.transicao || "")) return null;
            const arr = timeline.sfx_roles?.transicao;
            const src = arr && arr.length ? arr[i % arr.length] : timeline.click_rel!;
            const start = Math.max(0, Math.floor(c.inicio * fps) - 1);
            return (
              <Sequence key={`trans-${i}`} from={start} durationInFrames={Math.round(0.5 * fps)}>
                <Audio src={staticFile(src)} volume={0.8} />
              </Sequence>
            );
          })
        : null}
      {/* SFX — WHOOSH reverse SÓ no primeiro slide (abertura). Gated no glitch_topico (nicho calmo = sem whoosh). */}
      {timeline.glitch_topico !== false && timeline.sfx_roles?.first
        ? <Sequence from={0} durationInFrames={Math.round(2.0 * fps)}><Audio src={staticFile(timeline.sfx_roles.first)} volume={0.7} /></Sequence>
        : null}
      {/* SFX — SINO (alternado) na ENTRADA de infográfico/ilustração/pessoa */}
      {timeline.sfx_roles?.entrada?.length
        ? [
            ...timeline.cenas.filter((c) => c.infografico || c.ilustracao).map((c) => (c.aparece_em != null ? c.aparece_em : c.inicio)),
            ...(timeline.pessoas || []).map((p) => p.inicio),
          ].sort((a, b) => a - b).map((t, i) => {
            const arr = timeline.sfx_roles!.entrada!;
            return <Sequence key={`ent-${i}`} from={Math.max(0, Math.floor(t * fps) - 1)} durationInFrames={Math.round(1.2 * fps)}><Audio src={staticFile(arr[i % arr.length])} volume={0.5} /></Sequence>;
          })
        : null}
      {/* CAMADA SFX — RISER subindo até a fronteira de tópico (build-up p/ o glitch).
          Gated no glitch_topico: nicho calmo (false) NÃO tem riser/whoosh (Piter baniu esse SFX). */}
      {timeline.glitch_topico !== false && timeline.sfx_riser_rel
        ? (timeline.topicos || []).map((t, i) => {
            if (i === 0) return null;
            const riseDur = Math.round(1.9 * fps);   // riser_punch já sobe sozinho; pico (~1.4s) cai na fronteira
            const start = Math.max(0, Math.floor(t.inicio * fps) - Math.round(1.5 * fps));
            return (
              <Sequence key={`riser-${i}`} from={start} durationInFrames={riseDur}>
                <Audio src={staticFile(timeline.sfx_riser_rel!)} volume={0.5} />
              </Sequence>
            );
          })
        : null}

      {/* TRILHA em SEGMENTOS — corte seco por tópico + respiro de silêncio */}
      {(timeline.musica_segmentos && timeline.musica_segmentos.length
        ? timeline.musica_segmentos.map((s, i) => {
            const start = Math.floor(s.inicio * fps);
            const dur = Math.ceil((s.fim - s.inicio) * fps);
            const fadeF = Math.max(2, Math.round((s.fade || 0.4) * fps));
            return (
              <Sequence key={`mus-${i}`} from={start} durationInFrames={dur}>
                <Audio src={staticFile(s.track_rel)}
                  volume={(f) => (Number(timeline.__mute_music) ? 0 : s.vol) * interpolate(f, [0, fadeF, dur - fadeF, dur], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
              </Sequence>
            );
          })
        : timeline.musica_rel ? <Musica rel={timeline.musica_rel} env={timeline.musica_envelope} totalFrames={totalFrames} /> : null)}
    </AbsoluteFill>
  );
};
