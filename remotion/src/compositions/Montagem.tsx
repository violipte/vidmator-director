import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { NumberCountOverlay } from "./NumberCountOverlay";
import { MultiCountryOutline } from "./MultiCountryOutline";
import { ChapterTitle } from "./ChapterTitle";
import { BarChartComparison } from "./BarChartComparison";
import { DisplayText } from "./DisplayText";
import { MapRoute } from "./MapRoute";
import { SubjectTitleCard } from "./SubjectTitleCard";
import { BulletPointOverlay } from "./BulletPointOverlay";
import { LineChart } from "./LineChart";
import { CirclePercent } from "./CirclePercent";
import { SatelliteLocationPin } from "./SatelliteLocationPin";
import { OneWordCallout } from "./OneWordCallout";
import { GrowingBarChart } from "./GrowingBarChart";
import { LogoFlagGrid } from "./LogoFlagGrid";
import { QuoteCard } from "./QuoteCard";
import { TextReveal } from "./TextReveal";
import { SingleSentenceTextSlide } from "./SingleSentenceTextSlide";
import { TitleDescription } from "./TitleDescription";
import { CharacterCard } from "./CharacterCard";
import { SentenceHighlight } from "./SentenceHighlight";
import { TEXTO_COMPS } from "./texto/AcervoTexto";
import { OVERLAY_COMPS } from "./texto/AcervoTextoOverlay";
import { GRAFICOS_COMPS } from "./graficos/AcervoGraficos";
import { IMAGEM_COMPS } from "./imagem/AcervoImagem";
import { SOCIAL_COMPS } from "./social/AcervoSocial";
import { MAPAS_COMPS } from "./mapas/AcervoMapas";
import { DUO_COMPS } from "./duo/AcervoDuo";
import { LISTA_COMPS } from "./lista/AcervoListas";

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
  off_s?: number; trato?: string };

/* VidRush 24/07 (split de plano): 2º segmento do mesmo asset ganha offset + tratamento distinto */
const TRATOS: Record<string, string> = {
  pb: "grayscale(1) contrast(1.08) brightness(0.96)",
  tint: "sepia(0.30) saturate(1.25) contrast(1.04)",
  zoom: "",
};
type AudioPlan = { trilhas: { arquivo: string; t_ini: number; t_fim: number; vol: number }[];
  sfx: { arquivo: string; t: number; vol: number; dur: number }[] };
type Mont = { fps: number; dur_s: number; audio: string; secoes: any[]; beats: Beat[];
  estilo?: string; audio_plan?: AudioPlan };

const isVid = (s: string) => /\.(mp4|webm|mov)$/i.test(s);

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
const ClipFull: React.FC<{ src: string; off?: number; trato?: string }> = ({ src, off = 0, trato }) => {
  const { fps } = useVideoConfig();
  const filtro = trato ? TRATOS[trato] || "" : "";
  const escala = trato === "zoom" ? 1.24 : 1;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {isVid(src)
        ? <OffthreadVideo src={staticFile(src)} muted loop startFrom={Math.round(off * fps)}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: filtro || undefined, transform: escala !== 1 ? `scale(${escala})` : undefined }} />
        : <KenImg src={src} />}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 88% 88% at 50% 50%, transparent 58%, rgba(0,0,0,0.42) 100%)" }} />
    </AbsoluteFill>
  );
};

/* imagem/ilustração: Ken Burns lento */
const KenImg: React.FC<{ src: string }> = ({ src }) => {
  const f = useCurrentFrame();
  const s = 1.02 + Math.min(f / 1400, 0.09);
  return <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})` }} />;
};

const BeatView: React.FC<{ b: Beat; estilo?: string }> = ({ b, estilo = "v1" }) => {
  const durB = b.t_fim - b.t_ini;
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
        <KenImg src={b.src} />
      </AbsoluteFill>
    );
  }
  if (b.tier === 3) return <ClipT3 src={b.src} wm={b.watermark} i={b.i} secao={b.secao} estilo={estilo} durS={durB} />;
  return <ClipFull src={b.src} off={b.off_s || 0} trato={b.trato} />;
};

export const Montagem: React.FC<{ job?: string; mont?: Mont | null }> = ({ mont }) => {
  if (!mont) {
    return <AbsoluteFill style={{ background: "#0a0b0f", color: "#fff", alignItems: "center", justifyContent: "center", fontSize: 40 }}>montagem.json não carregado</AbsoluteFill>;
  }
  const fps = mont.fps || 30;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {mont.beats.map((b) => {
        const from = Math.round(b.t_ini * fps);
        const dur = Math.max(1, Math.round((b.t_fim - b.t_ini) * fps));
        const sec = mont.secoes.find((s) => s.i === b.secao);
        const wash = WASH[sec?.wash || "none"] || "transparent";
        return (
          <Sequence key={b.i} from={from} durationInFrames={dur}>
            <BeatView b={b} estilo={mont.estilo || "v1"} />
            {wash !== "transparent" && <AbsoluteFill style={{ background: wash, pointerEvents: "none" }} />}
          </Sequence>
        );
      })}
      <Audio src={staticFile(mont.audio)} />
      {/* ESTILO v2 [REGRAS_VDM §5.3]: trilha por momento (fade in/out, volume BAIXO) + SFX */}
      {(mont.audio_plan?.trilhas || []).map((t, i) => {
        const durT = Math.max(1, Math.round((t.t_fim - t.t_ini) * fps));
        return (
          <Sequence key={`tr${i}`} from={Math.round(t.t_ini * fps)} durationInFrames={durT}>
            <Audio src={staticFile(t.arquivo)} loop
              volume={(f) => interpolate(f, [0, 36, Math.max(37, durT - 50), durT],
                [0, t.vol, t.vol, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
          </Sequence>
        );
      })}
      {(mont.audio_plan?.sfx || []).map((s, i) => {
        const durS = Math.max(1, Math.round(s.dur * fps));
        return (
          <Sequence key={`sx${i}`} from={Math.round(s.t * fps)} durationInFrames={durS}>
            {/* fade-out nos últimos frames — corte de SFX nunca é seco */}
            <Audio src={staticFile(s.arquivo)}
              volume={(f) => interpolate(f, [0, 2, Math.max(3, durS - 9), durS],
                [0, s.vol, s.vol, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
          </Sequence>
        );
      })}
      {/* grão global leve */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.016) 0 2px, transparent 2px 4px)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
