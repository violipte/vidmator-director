import React from "react";
import { AbsoluteFill, Audio, Easing, Img, Loop, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { NumberCountOverlay } from "../NumberCountOverlay";
import { MultiCountryOutline } from "../MultiCountryOutline";
import { ChapterTitle } from "../ChapterTitle";
import { BarChartComparison } from "../BarChartComparison";
import { DisplayText } from "../DisplayText";
import { MapRoute } from "../MapRoute";
import { SubjectTitleCard } from "../SubjectTitleCard";
import { BulletPointOverlay } from "../BulletPointOverlay";
import { LineChart } from "../LineChart";
import { CirclePercent } from "../CirclePercent";
import { SatelliteLocationPin } from "../SatelliteLocationPin";
import { OneWordCallout } from "../OneWordCallout";
import { GrowingBarChart } from "../GrowingBarChart";
import { LogoFlagGrid } from "../LogoFlagGrid";
import { QuoteCard } from "../QuoteCard";
import { TextReveal } from "../TextReveal";
import { SingleSentenceTextSlide } from "../SingleSentenceTextSlide";
import { TitleDescription } from "../TitleDescription";
import { CharacterCard } from "../CharacterCard";
import { SentenceHighlight } from "../SentenceHighlight";
import { Mascot } from "../Mascot";
import { Parallax3Scene5 } from "./Parallax3Scene5";
import { ImageEffect5 } from "./ImageEffects5";
import { KenBurnsPro5 } from "./KenBurnsPro5";
import { Karaoke5 } from "./Karaoke5";
import { TEXTO_COMPS } from "../texto/AcervoTexto";
import { OVERLAY_COMPS } from "../texto/AcervoTextoOverlay";
import { GRAFICOS_COMPS } from "../graficos/AcervoGraficos";
import { IMAGEM_COMPS } from "../imagem/AcervoImagem";
import { SOCIAL_COMPS } from "../social/AcervoSocial";
import { MAPAS_COMPS } from "../mapas/AcervoMapas";
import { DUO_COMPS } from "../duo/AcervoDuo";
import { LISTA_COMPS } from "../lista/AcervoListas";

/* ============================================================
   MONTAGEM (Stage 4) — renderiza o montagem.json do montador.py:
   beats resolvidos (footage/stock/ilustração/animação) sincronizados
   com a narração + tratamento por tier + color-wash por seção.
   ============================================================ */

const COMP_MAP: Record<string, React.FC<any>> = {
  NumberCountOverlay, MultiCountryOutline, ChapterTitle, BarChartComparison, DisplayText,
  MapRoute, SubjectTitleCard, BulletPointOverlay, LineChart, CirclePercent,
  SatelliteLocationPin, OneWordCallout, GrowingBarChart, LogoFlagGrid, QuoteCard,
  TextReveal, SingleSentenceTextSlide, TitleDescription, CharacterCard, SentenceHighlight,
  // almoxarifado 2.0 — 79 variações curadas (Diretor sorteia por ID no registry)
  ...TEXTO_COMPS, ...OVERLAY_COMPS, ...GRAFICOS_COMPS, ...IMAGEM_COMPS, ...SOCIAL_COMPS, ...MAPAS_COMPS,
  ...DUO_COMPS, ...LISTA_COMPS,
};

const WASH: Record<string, string> = {
  teal: "rgba(20,184,166,0.10)", amarelo: "rgba(245,158,11,0.09)", vermelho: "rgba(220,38,38,0.10)",
  dourado: "rgba(217,119,6,0.10)", azul_frio: "rgba(59,130,246,0.10)", none: "transparent",
};

type Beat = { i: number; t_ini: number; t_fim: number; tipo: string; tier: number; watermark: boolean;
  secao: number; src?: string; bg?: string; bg_nitido?: boolean; componente?: string; props?: any;
  off_s?: number; trato?: string; trans_in?: { tipo: string };
  trans_out?: { tipo: string; dur_f: number };
  fx_img?: { tipo: string; accent?: string };
  kb?: string;
  captionWords?: { word: string; startFrame: number }[];
  mascote?: { img: string; lado: "left" | "right"; altura: number; pose?: string } };

/* VidRush 24/07 (split de plano): 2º segmento do mesmo asset ganha offset + tratamento distinto */
const TRATOS: Record<string, string> = {
  pb: "grayscale(1) contrast(1.08) brightness(0.96)",
  tint: "sepia(0.30) saturate(1.25) contrast(1.04)",
  zoom: "",
};
type AudioPlan = { trilhas: { arquivo: string; t_ini: number; t_fim: number; vol: number }[];
  sfx: { arquivo: string; t: number; vol: number; dur: number }[] };
type FxOverlay = { arquivo: string; t_ini: number; t_fim: number; modo: string; op: number; dur_s: number };
type FxTrans = { t: number; tipo: string; arquivo?: string; pico_s?: number; dur_s?: number };
type Mont = { fps: number; dur_s: number; audio: string; secoes: any[]; beats: Beat[];
  estilo?: string; audio_plan?: AudioPlan; fx_overlays?: FxOverlay[]; fx_trans?: FxTrans[];
  avatar_ilhas?: { t_ini: number; t_fim: number }[] };

const isVid = (s: string) => /\.(mp4|webm|mov)$/i.test(s);

/* v5 F2: transição NATIVA de saída — o beat que SAI é estendido dur_f frames além
   do corte e anima por cima do beat entrante (que já roda embaixo): conteúdo VIVO
   dos dois lados, como o TransitionSeries, sem reestruturar a timeline. */
const TransOutWrap: React.FC<{ to?: { tipo: string; dur_f: number };
  durBase: number; children: React.ReactNode }> = ({ to, durBase, children }) => {
  const f = useCurrentFrame();
  if (!to) return <>{children}</>;
  const ini = durBase;                       // frame local onde o corte nominal acontece
  const fim = durBase + to.dur_f;
  const p = interpolate(f, [ini, fim], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  let estilo: React.CSSProperties = {};
  if (to.tipo === "fade") {
    estilo = { opacity: 1 - p };
  } else if (to.tipo === "slidePush") {
    estilo = { opacity: 1 - p * 0.4, transform: `translateX(${-p * 34}%)` };
  } else if (to.tipo === "blurCut") {
    estilo = { opacity: 1 - p, filter: `blur(${p * 16}px)` };
  }
  return <AbsoluteFill style={{ ...estilo, zIndex: 5 }}>{children}</AbsoluteFill>;
};

/* v2.1 [28/07 — acervo da equipe]: transform de ENTRADA no 1º beat da seção.
   Receitas do manifesto (zoom_whammy, deslizar, tremor, gire) em CSS puro. */
const TransInWrap: React.FC<{ tipo?: string; children: React.ReactNode }> = ({ tipo, children }) => {
  const f = useCurrentFrame();
  let tf = "";
  if (tipo === "zoom_whammy") {
    tf = `scale(${interpolate(f, [0, 12], [1.3, 1], { extrapolateRight: "clamp" })})`;
  } else if (tipo === "deslizar_esquerda") {
    tf = `translateX(${interpolate(f, [0, 12], [180, 0], { extrapolateRight: "clamp" })}px)`;
  } else if (tipo === "deslizar_baixo") {
    tf = `translateY(${interpolate(f, [0, 12], [-180, 0], { extrapolateRight: "clamp" })}px)`;
  } else if (tipo === "gire_cw") {
    const r = interpolate(f, [0, 14], [-5, 0], { extrapolateRight: "clamp" });
    const z = interpolate(f, [0, 14], [1.1, 1], { extrapolateRight: "clamp" });
    tf = `rotate(${r}deg) scale(${z})`;
  } else if (tipo === "tremor" || tipo === "sacudir") {
    const amp = interpolate(f, [0, 14], [tipo === "sacudir" ? 24 : 14, 0], { extrapolateRight: "clamp" });
    tf = `translate(${Math.sin(f * 2.3) * amp}px, ${Math.cos(f * 1.7) * amp * 0.6}px)`;
  }
  if (!tf) return <>{children}</>;
  return <AbsoluteFill style={{ transform: tf }}>{children}</AbsoluteFill>;
};

/* v2.1: veils de transição (flash/fade/blur/ink) — camada global por cima do corte.
   Tipos transform retornam null aqui (agem via trans_in no beat). */
const VeilFX: React.FC<{ fx: FxTrans }> = ({ fx }) => {
  const f = useCurrentFrame();
  if (fx.tipo === "veil_video" && fx.arquivo) {
    return (
      <AbsoluteFill style={{ mixBlendMode: "multiply", pointerEvents: "none" }}>
        <OffthreadVideo src={staticFile(fx.arquivo)} muted
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }} />
      </AbsoluteFill>
    );
  }
  if (fx.tipo === "flash_branco" || fx.tipo === "flash_crescente") {
    const [durF, pico] = fx.tipo === "flash_branco" ? [12, 4] : [22, 14];
    const o = interpolate(f, [0, pico, durF - 1], [0, 0.9, 0], { extrapolateRight: "clamp" });
    return <AbsoluteFill style={{ background: "#fff", opacity: o, pointerEvents: "none" }} />;
  }
  if (fx.tipo === "esmaecer_preto" || fx.tipo === "suave") {
    const [durF, teto] = fx.tipo === "esmaecer_preto" ? [24, 1] : [14, 0.65];
    const o = interpolate(f, [0, durF * 0.42, durF * 0.58, durF - 1], [0, teto, teto, 0],
      { extrapolateRight: "clamp" });
    return <AbsoluteFill style={{ background: "#000", opacity: o, pointerEvents: "none" }} />;
  }
  if (fx.tipo === "blur_dip") {
    const px = interpolate(f, [0, 8, 17], [0, 14, 0], { extrapolateRight: "clamp" });
    return <AbsoluteFill style={{ backdropFilter: `blur(${px}px)`, pointerEvents: "none" }} />;
  }
  return null;
};
const veilLeadF = (fx: FxTrans, fps: number) =>
  fx.tipo === "veil_video" ? Math.round((fx.pico_s ?? 1) * fps) :
  fx.tipo === "flash_crescente" ? 14 : fx.tipo === "esmaecer_preto" ? 10 :
  fx.tipo === "suave" ? 6 : fx.tipo === "blur_dip" ? 8 : 4;
const veilDurF = (fx: FxTrans, fps: number) =>
  fx.tipo === "veil_video" ? Math.max(1, Math.round((fx.dur_s ?? 3) * fps)) :
  fx.tipo === "flash_crescente" ? 22 : fx.tipo === "esmaecer_preto" ? 24 :
  fx.tipo === "suave" ? 14 : fx.tipo === "blur_dip" ? 18 : 12;

/* footage T3: quadro menor + grid de fundo (receita §5.1); watermark -> zoom interno (crop).
   QA tenis 23/07 (Piter): gradiente e moldura eram SEMPRE iguais — agora 4 paletas escuras
   (por seção) x 3 formatos de quadro (por beat), determinístico. */
const T3_TEMAS = [
  { bg: "radial-gradient(ellipse 90% 90% at 50% 46%, #0c1120 0%, #05060a 100%)", borda: "rgba(150,180,255,0.75)", glow: "rgba(150,180,255,0.35)", grid: "rgba(140,160,220,0.10)" },
  { bg: "radial-gradient(ellipse 90% 90% at 50% 46%, #191309 0%, #0a0704 100%)", borda: "rgba(245,196,120,0.7)", glow: "rgba(245,158,11,0.30)", grid: "rgba(220,180,130,0.09)" },
  { bg: "radial-gradient(ellipse 90% 90% at 50% 46%, #0e1913 0%, #04080a 100%)", borda: "rgba(140,220,180,0.65)", glow: "rgba(52,211,153,0.30)", grid: "rgba(140,210,175,0.09)" },
  { bg: "linear-gradient(160deg, #16121c 0%, #08060c 100%)", borda: "rgba(200,168,255,0.6)", glow: "rgba(170,120,255,0.30)", grid: "rgba(180,150,230,0.08)" },
];

const ClipT3: React.FC<{ src: string; wm: boolean; i?: number; secao?: number; estilo?: string; durS?: number }> =
  ({ src, wm, i = 0, secao = 0, estilo = "v1", durS = 4 }) => {
  const f = useCurrentFrame();
  const inner = wm ? 1.28 : 1.04 + Math.min(f / 900, 0.05);
  const tema = T3_TEMAS[secao % T3_TEMAS.length];
  const shape = i % 3;

  // ===== ESTILO v2 [REGRAS_VDM §4]: máscaras T3 rotativas =====
  if (estilo === "v2") {
    if (isVid(src)) {
      const v2s = i % 4;
      if (v2s === 1) {
        // blur cinemático: fundo = o próprio vídeo borrado, centro nítido
        return (
          <AbsoluteFill style={{ background: "#000" }}>
            <OffthreadVideo src={staticFile(src)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(26px) brightness(0.55)", transform: "scale(1.12)" }} />
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
              <div style={{ width: "82%", height: "82%", borderRadius: 8, overflow: "hidden", boxShadow: "0 30px 90px rgba(0,0,0,0.75)" }}>
                <OffthreadVideo src={staticFile(src)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${inner})` }} />
              </div>
            </AbsoluteFill>
          </AbsoluteFill>
        );
      }
      if (v2s === 2) {
        // faixa preta (letterbox cinemático)
        return (
          <AbsoluteFill style={{ background: "#000", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: "100%", height: "72%", overflow: "hidden" }}>
              <OffthreadVideo src={staticFile(src)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${inner})` }} />
            </div>
          </AbsoluteFill>
        );
      }
      if (v2s === 3) {
        // câmera antiga: sépia leve + viewfinder REC
        return (
          <AbsoluteFill style={{ background: "#000" }}>
            <OffthreadVideo src={staticFile(src)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(0.35) contrast(1.08) brightness(0.95)", transform: `scale(${inner})` }} />
            <AbsoluteFill style={{ border: "26px solid rgba(0,0,0,0.35)" }} />
            <div style={{ position: "absolute", top: 42, left: 56, display: "flex", alignItems: "center", gap: 12, fontFamily: "monospace", fontSize: 30, color: "#fff", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>
              <div style={{ width: 18, height: 18, borderRadius: 9, background: "#ef4444", opacity: Math.floor(f / 15) % 2 ? 1 : 0.25 }} />REC
            </div>
            <div style={{ position: "absolute", top: 42, right: 56, fontFamily: "monospace", fontSize: 26, color: "#fff", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>PLAY ▸</div>
          </AbsoluteFill>
        );
      }
      // v2s === 0 cai no grid padrão abaixo
    } else {
      const v2i = i % 3;
      if (v2i === 1 || (v2i === 2 && durS > 2.6)) {
        // vinheta + zoom dramático de 2s no ponto de importância (centro)
        const z = interpolate(f, [0, 60], [1.35, 1.0], { extrapolateRight: "clamp" });
        return (
          <AbsoluteFill style={{ background: "#000" }}>
            <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})` }} />
            <AbsoluteFill style={{ background: "radial-gradient(ellipse 70% 70% at 50% 50%, transparent 40%, rgba(0,0,0,0.72) 100%)" }} />
          </AbsoluteFill>
        );
      }
      if (v2i === 2) {
        // full screen com passagem rápida (≤2.6s, garantido acima)
        const z = 1.02 + Math.min(f / 500, 0.1);
        return (
          <AbsoluteFill style={{ background: "#000" }}>
            <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, filter: wm ? "blur(0px)" : undefined }} />
          </AbsoluteFill>
        );
      }
      // v2i === 0 cai no grid padrão abaixo
    }
  }
  const quadro: React.CSSProperties = shape === 1
    ? { width: "100%", height: "64%", borderRadius: 0, borderTop: `2px solid ${tema.borda}`, borderBottom: `2px solid ${tema.borda}` }
    : shape === 2
      ? { width: "63%", height: "78%", borderRadius: 10, border: `3px solid ${tema.borda}`, transform: "rotate(-1.2deg)" }
      : { width: "72%", height: "72%", borderRadius: 14, border: `2px solid ${tema.borda}` };
  return (
    <AbsoluteFill style={{ background: tema.bg }}>
      <AbsoluteFill style={{
        backgroundImage: `repeating-linear-gradient(0deg, ${tema.grid} 0 1px, transparent 1px 72px), repeating-linear-gradient(90deg, ${tema.grid} 0 1px, transparent 1px 72px)`,
      }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ ...quadro, overflow: "hidden",
          boxShadow: `0 26px 80px rgba(0,0,0,0.7), 0 0 36px ${tema.glow}`, background: "#000" }}>
          {isVid(src)
            ? <OffthreadVideo src={staticFile(src)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${inner})` }} />
            : <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${inner})` }} />}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 4px)", opacity: 0.45 }} />
    </AbsoluteFill>
  );
};

/* footage T1/stock: full-frame + vinheta leve. off/trato = split de plano (VidRush) */
const ClipFull: React.FC<{ src: string; off?: number; trato?: string; kb?: string }> = ({ src, off = 0, trato, kb }) => {
  const { fps } = useVideoConfig();
  const filtro = trato ? TRATOS[trato] || "" : "";
  const escala = trato === "zoom" ? 1.24 : 1;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {isVid(src)
        ? <OffthreadVideo src={staticFile(src)} muted loop startFrom={Math.round(off * fps)}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: filtro || undefined, transform: escala !== 1 ? `scale(${escala})` : undefined }} />
        : <KenImg src={src} kb={kb} />}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 88% 88% at 50% 50%, transparent 58%, rgba(0,0,0,0.42) 100%)" }} />
    </AbsoluteFill>
  );
};

/* imagem/ilustração: Ken Burns — v5 F4: com `kb` usa o tipo SEMÂNTICO (11 variações) */
const KenImg: React.FC<{ src: string; kb?: string }> = ({ src, kb }) => {
  const f = useCurrentFrame();
  if (kb) return <KenBurnsPro5 src={src} kb={kb} />;
  const s = 1.02 + Math.min(f / 1400, 0.09);
  return <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})` }} />;
};

const BeatView: React.FC<{ b: Beat; estilo?: string }> = ({ b, estilo = "v1" }) => {
  const durB = b.t_fim - b.t_ini;
  if (b.tipo === "parallax") {
    // v5: cena 2.5D de camadas (fundo/meio/frente geradas + recortadas)
    return <Parallax3Scene5 {...((b.props || {}) as object)} />;
  }
  if (b.tipo === "avatar" && b.src) {
    // AVATAR v3 (29/07): apresentador do Flow — full-frame COM áudio nativo
    // (a narração ducka nesta janela; ver volume do <Audio> principal)
    return (
      <AbsoluteFill style={{ background: "#000" }}>
        <OffthreadVideo src={staticFile(b.src)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
    );
  }
  if (b.tipo === "animacao") {
    const C = COMP_MAP[b.componente || ""] || DisplayText;
    if (b.bg) {
      // bg_nitido (R-27): footage VISÍVEL sob overlay de data — sem blur, só leve escurecida
      const fx = b.bg_nitido ? "brightness(0.62)" : "blur(7px) brightness(0.38)";
      return (
        <AbsoluteFill style={{ background: "#0a0b0f" }}>
          {isVid(b.bg)
            ? <OffthreadVideo src={staticFile(b.bg)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover", filter: fx, transform: b.bg_nitido ? undefined : "scale(1.06)" }} />
            : <Img src={staticFile(b.bg)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: fx, transform: b.bg_nitido ? undefined : "scale(1.06)" }} />}
          <C {...(b.props || {})} />
        </AbsoluteFill>
      );
    }
    return <C {...(b.props || {})} />;
  }
  if (!b.src) return <AbsoluteFill style={{ background: "#0a0b0f" }} />;
  if (b.tipo === "ilustracao") {
    // R-105: ilustração REAL da web (T3) leva máscara PESADA (frame+grid+crop interno);
    // gerada por IA (T0) segue full-frame
    if (b.tier === 3) return <ClipT3 src={b.src} wm={true} i={b.i} secao={b.secao} estilo={estilo} durS={durB} />;
    return (
      <AbsoluteFill style={{ background: "#0a0b0f" }}>
        <KenImg src={b.src} kb={b.kb} />
      </AbsoluteFill>
    );
  }
  if (b.tier === 3) return <ClipT3 src={b.src} wm={b.watermark} i={b.i} secao={b.secao} estilo={estilo} durS={durB} />;
  return <ClipFull src={b.src} off={b.off_s || 0} trato={b.trato} kb={b.kb} />;
};

export const Montagem5: React.FC<{ job?: string; mont?: Mont | null }> = ({ mont }) => {
  if (!mont) {
    return <AbsoluteFill style={{ background: "#0a0b0f", color: "#fff", alignItems: "center", justifyContent: "center", fontSize: 40 }}>montagem.json não carregado</AbsoluteFill>;
  }
  const fps = mont.fps || 30;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {mont.beats.map((b) => {
        const from = Math.round(b.t_ini * fps);
        const durBase = Math.max(1, Math.round((b.t_fim - b.t_ini) * fps));
        const dur = durBase + (b.trans_out?.dur_f || 0);  // v5: estende p/ transição viva
        const sec = mont.secoes.find((s) => s.i === b.secao);
        const wash = WASH[sec?.wash || "none"] || "transparent";
        return (
          <Sequence key={b.i} from={from} durationInFrames={dur}>
            <TransOutWrap to={b.trans_out} durBase={durBase}>
              <TransInWrap tipo={b.trans_in?.tipo}>
                <BeatView b={b} estilo={mont.estilo || "v1"} />
                {/* v5 F3: efeito CSS por beat (grade/animado, zero asset) */}
                {b.fx_img && <ImageEffect5 tipo={b.fx_img.tipo} accent={b.fx_img.accent} />}
                {wash !== "transparent" && <AbsoluteFill style={{ background: wash, pointerEvents: "none" }} />}
                {/* MASCOTE opcional (28/07): personagem do canal por cima do beat */}
                {b.mascote && (
                  <Mascot imgRel={b.mascote.img} lado={b.mascote.lado}
                    sceneFrames={dur} alturaFrac={b.mascote.altura} />
                )}
                {/* v5 F5: karaokê word-by-word (opcional por style_card) */}
                {b.captionWords && <Karaoke5 words={b.captionWords} accent={(b.fx_img?.accent) || "#f59e0b"} />}
              </TransInWrap>
            </TransOutWrap>
          </Sequence>
        );
      })}
      {/* v2.1: OVERLAYS de textura do acervo (screen/multiply, opacity baixa, loop) */}
      {(mont.fx_overlays || []).map((o, i) => {
        const durO = Math.max(1, Math.round((o.t_fim - o.t_ini) * fps));
        const durArq = Math.max(1, Math.round(o.dur_s * fps));
        return (
          <Sequence key={`fxo${i}`} from={Math.round(o.t_ini * fps)} durationInFrames={durO}>
            <AbsoluteFill style={{ mixBlendMode: o.modo as any, opacity: o.op, pointerEvents: "none" }}>
              <Loop durationInFrames={durArq}>
                <OffthreadVideo src={staticFile(o.arquivo)} muted
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </Loop>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {/* v2.1: TRANSITIONS nos cortes de seção (veils; transforms agem via trans_in) */}
      {(mont.fx_trans || []).map((fx, i) => (
        <Sequence key={`fxt${i}`} from={Math.max(0, Math.round(fx.t * fps) - veilLeadF(fx, fps))}
          durationInFrames={veilDurF(fx, fps)}>
          <VeilFX fx={fx} />
        </Sequence>
      ))}
      <Audio src={staticFile(mont.audio)}
        volume={(f) => {
          // AVATAR v3: narração DUCKA nas ilhas de apresentador (áudio nativo do clipe)
          for (const il of mont.avatar_ilhas || []) {
            const a = Math.round(il.t_ini * fps) - 3;
            const b = Math.round(il.t_fim * fps) + 3;
            if (f >= a && f <= b) return 0.06;
          }
          return 1;
        }} />
      {/* ESTILO v2 [REGRAS_VDM §5.3]: trilha por momento (fade in/out, volume BAIXO) + SFX */}
      {(mont.audio_plan?.trilhas || []).map((t, i) => {
        const durT = Math.max(1, Math.round((t.t_fim - t.t_ini) * fps));
        return (
          <Sequence key={`tr${i}`} from={Math.round(t.t_ini * fps)} durationInFrames={durT}>
            <Audio src={staticFile(t.arquivo)} loop
              volume={(f) => {
                // keyframes sempre monotônicos, mesmo com trecho curto (crash frame 303, 27/07)
                const a = Math.min(36, Math.max(1, durT * 0.3));
                const b = Math.max(a + 1, durT - 50);
                return interpolate(f, [0, a, b, Math.max(b + 1, durT)],
                  [0, t.vol, t.vol, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              }} />
          </Sequence>
        );
      })}
      {(mont.audio_plan?.sfx || []).map((s, i) => {
        const durS = Math.max(1, Math.round(s.dur * fps));
        return (
          <Sequence key={`sx${i}`} from={Math.round(s.t * fps)} durationInFrames={durS}>
            {/* fade-out nos últimos frames — corte de SFX nunca é seco */}
            <Audio src={staticFile(s.arquivo)}
              volume={(f) => {
                const a = Math.min(2, Math.max(1, durS * 0.3));
                const b = Math.max(a + 1, durS - 9);
                return interpolate(f, [0, a, b, Math.max(b + 1, durS)],
                  [0, s.vol, s.vol, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              }} />
          </Sequence>
        );
      })}
      {/* grão global leve */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.016) 0 2px, transparent 2px 4px)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
