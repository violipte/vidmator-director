import { Composition } from "remotion";
import { CtaCard, ctaCardSchema } from "./compositions/CtaCard";
import { CrossfadeTransition } from "./compositions/CrossfadeTransition";
import { SlideHorizontalTransition } from "./compositions/SlideHorizontalTransition";
import { WhipPanTransition } from "./compositions/WhipPanTransition";
import { SmoothZoomTransition } from "./compositions/SmoothZoomTransition";
import { LightRays } from "./compositions/LightRays";
import { ParticlesDrift } from "./compositions/ParticlesDrift";
import { StarsDrifting } from "./compositions/StarsDrifting";
import { AuroraGlow } from "./compositions/AuroraGlow";
import { LightLeak } from "./compositions/LightLeak";
import { CtaCardSide } from "./compositions/CtaCardSide";
import { CtaBannerSlim } from "./compositions/CtaBannerSlim";
import { CtaPopupCenter } from "./compositions/CtaPopupCenter";
import { WordByWordReveal } from "./compositions/WordByWordReveal";
import { SubscribeBellPulse } from "./compositions/SubscribeBellPulse";
import { SubscribeMinimal } from "./compositions/SubscribeMinimal";
import { BrollTest } from "./compositions/BrollTest";
import { MapAnimation } from "./compositions/MapAnimation";
import { SatelliteZoom } from "./compositions/SatelliteZoom";
import { DoodleGallery } from "./compositions/DoodleGallery";
import { AnimatedIcons } from "./compositions/AnimatedIcons";
import { DataViz } from "./compositions/DataViz";
import { CardsStructure } from "./compositions/CardsStructure";
import { ArchiveDemo } from "./compositions/ArchiveClip";
import { PersonCard } from "./compositions/PersonCard";
import { ImageStyleDemo } from "./compositions/ImageCard";
import { PresentationGallery } from "./compositions/PresentationGallery";
import { SfxSampler } from "./compositions/SfxSampler";
import { ExerciseGallery } from "./compositions/ExerciseAnim";
import { TypewriterIntro, TypewriterQuote } from "./compositions/TypewriterQuote";
import { EditMaskDemo } from "./compositions/EditMask";
import { ProductCTAMock } from "./compositions/ProductCTA";
import { StatReveal } from "./compositions/StatReveal";
import { VintageAngled } from "./compositions/VintageAngled";
import { FramedGridMontage } from "./compositions/FramedGridMontage";
import { Montagem } from "./compositions/Montagem";
import { Montagem5 } from "./compositions/v5/Montagem5";
import { TEXTO_COMPS } from "./compositions/texto/AcervoTexto";
import { OVERLAY_COMPS } from "./compositions/texto/AcervoTextoOverlay";
import { GRAFICOS_COMPS } from "./compositions/graficos/AcervoGraficos";
import { IMAGEM_COMPS } from "./compositions/imagem/AcervoImagem";
import { SOCIAL_COMPS } from "./compositions/social/AcervoSocial";
import { MAPAS_COMPS } from "./compositions/mapas/AcervoMapas";
import { FontePrancha } from "./compositions/FontePrancha";
import { AbsoluteFill, OffthreadVideo, Img } from "remotion";

const TextoPreview: React.FC<{ variante?: string; text?: string; kicker?: string; accent?: string }> = ({ variante = "Texto01_Typewriter", ...p }) => {
  const C = TEXTO_COMPS[variante] || TEXTO_COMPS.Texto01_Typewriter;
  return <C {...p} />;
};

const GraficoPreview: React.FC<{ variante?: string; bg?: string; dim?: number; title?: string; kicker?: string; accent?: string; labels?: string[]; values?: number[]; suffix?: string }> = ({ variante = "Graf01_CounterGlow", bg = "", dim = 0, ...p }) => {
  const C = GRAFICOS_COMPS[variante] || GRAFICOS_COMPS.Graf01_CounterGlow;
  if (!bg) return <C {...p} />;
  const ehVideo = /\.(mp4|webm|mov)$/i.test(bg);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {ehVideo
        ? <OffthreadVideo src={staticFile(bg)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        : <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
      {dim > 0 ? <AbsoluteFill style={{ background: `rgba(0,0,0,${Math.min(dim, 0.85)})` }} /> : null}
      <C {...p} />
    </AbsoluteFill>
  );
};

const ImagemPreview: React.FC<{ variante?: string; images?: string[]; captions?: string[]; title?: string; kicker?: string; accent?: string }> = ({ variante = "Img01_KenBurnsCine", ...p }) => {
  const C = IMAGEM_COMPS[variante] || IMAGEM_COMPS.Img01_KenBurnsCine;
  return <C {...p} />;
};

const SocialPreview: React.FC<{ variante?: string; autor?: string; handle?: string; titulo?: string; texto?: string; grifo?: string; imagem?: string; curtidas?: number; kicker?: string; accent?: string }> = ({ variante = "Soc01_InstagramDM", ...p }) => {
  const C = SOCIAL_COMPS[variante] || SOCIAL_COMPS.Soc01_InstagramDM;
  return <C {...p} />;
};

const MapaPreview: React.FC<{ variante?: string; paises?: string[]; pontos?: { nome?: string; lat: number; lon: number }[]; valores?: string[]; titulo?: string; kicker?: string; accent?: string; sat?: string[]; halfs?: number[]; bbox?: number[]; images?: string[] }> = ({ variante = "Map01_CountryFocus", ...p }) => {
  const C = MAPAS_COMPS[variante] || MAPAS_COMPS.Map01_CountryFocus;
  return <C {...p} />;
};

const TextoOverlayPreview: React.FC<{ variante?: string; bg?: string; dim?: number; text?: string; kicker?: string; accent?: string }> = ({ variante = "Ovl01_ChapterBig", bg = "", dim = 0, ...p }) => {
  const C = OVERLAY_COMPS[variante] || OVERLAY_COMPS.Ovl01_ChapterBig;
  const ehVideo = /\.(mp4|webm|mov)$/i.test(bg);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {bg ? (ehVideo
        ? <OffthreadVideo src={staticFile(bg)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        : <Img src={staticFile(bg)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />) : null}
      {dim > 0 ? <AbsoluteFill style={{ background: `rgba(0,0,0,${Math.min(dim, 0.85)})` }} /> : null}
      <C {...p} />
    </AbsoluteFill>
  );
};
import { staticFile } from "remotion";
import { PercentageBarChart } from "./compositions/PercentageBarChart";
import { PieChart } from "./compositions/PieChart";
import { LineChart } from "./compositions/LineChart";
import { GrowingBarChart } from "./compositions/GrowingBarChart";
import { BarChartComparison } from "./compositions/BarChartComparison";
import { CirclePercent } from "./compositions/CirclePercent";
import { NumberCountOverlay } from "./compositions/NumberCountOverlay";
import { StockChart } from "./compositions/StockChart";
import { PriceCallOut } from "./compositions/PriceCallOut";
import { ObjectDualStat } from "./compositions/ObjectDualStat";
import { PollSurveyBar } from "./compositions/PollSurveyBar";
import { OneWordCallout } from "./compositions/OneWordCallout";
import { IconGrid } from "./compositions/IconGrid";
import { IconLabels } from "./compositions/IconLabels";
import { CircleHighlight } from "./compositions/CircleHighlight";
import { BulletPointOverlay } from "./compositions/BulletPointOverlay";
import { MultiCountryOutline } from "./compositions/MultiCountryOutline";
import { SatelliteDrawPath } from "./compositions/SatelliteDrawPath";
import { MapRoute } from "./compositions/MapRoute";
import { SatelliteLocationPin } from "./compositions/SatelliteLocationPin";
import { RegionLocationText } from "./compositions/RegionLocationText";
import { CountryCharacterMap } from "./compositions/CountryCharacterMap";
import { SentenceHighlight } from "./compositions/SentenceHighlight";
import { TextReveal } from "./compositions/TextReveal";
import { TitleDescription } from "./compositions/TitleDescription";
import { QuoteCard } from "./compositions/QuoteCard";
import { ChapterTitle } from "./compositions/ChapterTitle";
import { DisplayText } from "./compositions/DisplayText";
import { DateLocationOverlay } from "./compositions/DateLocationOverlay";
import { CaptionTextOverlay } from "./compositions/CaptionTextOverlay";
import { DualImpactSentence } from "./compositions/DualImpactSentence";
import { SingleSentenceTextSlide } from "./compositions/SingleSentenceTextSlide";
import { CharacterCard } from "./compositions/CharacterCard";
import { CharacterKeyword } from "./compositions/CharacterKeyword";
import { ObjectTitle } from "./compositions/ObjectTitle";
import { NodeHierarchy } from "./compositions/NodeHierarchy";
import { SubjectTitleCard } from "./compositions/SubjectTitleCard";
import { DetectiveBoard } from "./compositions/DetectiveBoard";
import { InstagramConversation } from "./compositions/InstagramConversation";
import { TwoImageComparison } from "./compositions/TwoImageComparison";
import { ThreeImageReveal } from "./compositions/ThreeImageReveal";
import { FourImageSlideshow } from "./compositions/FourImageSlideshow";
import { MultiImageCutText } from "./compositions/MultiImageCutText";
import { DualImageOnGrid } from "./compositions/DualImageOnGrid";
import { SplitScreenComparison } from "./compositions/SplitScreenComparison";
import { FourImageCaptionGrid } from "./compositions/FourImageCaptionGrid";
import { FiveTextListicle } from "./compositions/FiveTextListicle";
import { BeforeAfterArrow } from "./compositions/BeforeAfterArrow";
import { ImageTextAnnotation } from "./compositions/ImageTextAnnotation";
import { WebsiteScreenshotReveal } from "./compositions/WebsiteScreenshotReveal";
import { ArticleNewsCard } from "./compositions/ArticleNewsCard";
import { LogoFlagGrid } from "./compositions/LogoFlagGrid";
import { ImageCallout } from "./compositions/ImageCallout";
import { PaperMovingTransparentObject } from "./compositions/PaperMovingTransparentObject";
import { GalleryReel, REEL_FRAMES } from "./compositions/GalleryReel";

// 1280×720 30fps — preview catálogo
const W = 1280;
const H = 720;
const FPS = 30;
const SHORT = 90;   // 3s
const MED = 105;    // 3.5s

export const Root: React.FC = () => {
  return (
    <>
      {/* Transições (cena A → cena B) */}
      <Composition id="01-CrossfadeTransition" component={CrossfadeTransition} durationInFrames={SHORT} fps={FPS} width={W} height={H} />
      <Composition id="02-SlideHorizontalTransition" component={SlideHorizontalTransition} durationInFrames={SHORT} fps={FPS} width={W} height={H} />
      <Composition id="03-WhipPanTransition" component={WhipPanTransition} durationInFrames={SHORT} fps={FPS} width={W} height={H} />
      <Composition id="04-SmoothZoomTransition" component={SmoothZoomTransition} durationInFrames={SHORT} fps={FPS} width={W} height={H} />

      {/* Efeitos do nicho cosmic/starseed */}
      <Composition id="05-LightRays" component={LightRays} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="06-ParticlesDrift" component={ParticlesDrift} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="07-StarsDrifting" component={StarsDrifting} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="08-AuroraGlow" component={AuroraGlow} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="09-LightLeak" component={LightLeak} durationInFrames={MED} fps={FPS} width={W} height={H} />

      {/* CTAs (3 variações) */}
      <Composition id="10-CtaCardSide" component={CtaCardSide} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="11-CtaBannerSlim" component={CtaBannerSlim} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="12-CtaPopupCenter" component={CtaPopupCenter} durationInFrames={MED} fps={FPS} width={W} height={H} />

      {/* Texto animado */}
      <Composition id="13-WordByWordReveal" component={WordByWordReveal} durationInFrames={MED} fps={FPS} width={W} height={H} />

      {/* Inscreva-se */}
      <Composition id="14-SubscribeBellPulse" component={SubscribeBellPulse} durationInFrames={MED} fps={FPS} width={W} height={H} />
      <Composition id="15-SubscribeMinimal" component={SubscribeMinimal} durationInFrames={MED} fps={FPS} width={W} height={H} />

      {/* Teste B-roll dinâmico (Fase 1) — lê timeline via inputProps */}
      <Composition
        id="BrollTest"
        component={BrollTest}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ timeline: null }}
        calculateMetadata={({ props }) => {
          const dur = (props.timeline && props.timeline.duracao) || 10;
          return { durationInFrames: Math.ceil(dur * 30) };
        }}
      />

      {/* PoC: animação de mapa (zoom -> país -> pin -> linha -> imagem) */}
      <Composition
        id="MapPoc"
        component={MapAnimation}
        durationInFrames={195}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ pais: "Egypt", coord: [31.24, 30.04] as [number, number], legenda: "Ancient Egypt", imagem_rel: "test/map_img.jpg" }}
      />

      {/* PoC: zoom de satélite cinematográfico (Google Earth style, ESRI imagery) */}
      <Composition
        id="SatelliteZoom"
        component={SatelliteZoom}
        durationInFrames={225}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Galeria de doodles (amostra de estilos hand-drawn) */}
      <Composition
        id="DoodleGallery"
        component={DoodleGallery}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Galeria de ícones de conceito animados */}
      <Composition id="AnimatedIcons" component={AnimatedIcons} durationInFrames={130} fps={30} width={1920} height={1080} />
      {/* Galeria de dados & gráficos animados */}
      <Composition id="DataViz" component={DataViz} durationInFrames={140} fps={30} width={1920} height={1080} />
      {/* Galeria de cards & estrutura */}
      <Composition id="CardsStructure" component={CardsStructure} durationInFrames={150} fps={30} width={1920} height={1080} />
      {/* Demo footage de arquivo (fundir + enquadrar) */}
      <Composition id="ArchiveDemo" component={ArchiveDemo} durationInFrames={300} fps={30} width={1920} height={1080} />
      {/* Demo dos 3 estilos de imagem PD (clipping / split / photo) */}
      <Composition id="ImageStyleDemo" component={ImageStyleDemo} durationInFrames={360} fps={30} width={1920} height={1080} />
      {/* Galeria das 8 apresentações de imagem/vídeo (lupa, spotlight, split, grid, polaroid, film, parallax, reveal) */}
      <Composition id="PresentationGallery" component={PresentationGallery} durationInFrames={840} fps={30} width={1920} height={1080} />
      {/* Sampler de SFX p/ avaliação (entrada de elementos + transições) */}
      <Composition id="SfxSampler" component={SfxSampler} durationInFrames={1320} fps={30} width={1920} height={1080} />
      {/* Galeria de demonstrações de exercício animadas (nicho saúde/fitness) */}
      <Composition id="ExerciseGallery" component={ExerciseGallery} durationInFrames={1596} fps={30} width={1920} height={1080} />
      {/* Cold open dramático: frase filosófica em typewriter + noise de TV (nicho fitness/espiritual) */}
      <Composition id="TypewriterIntro" component={TypewriterIntro} durationInFrames={240} fps={30} width={1920} height={1080} />
      {/* Cold open PARAMETRIZADO: quote/author via inputProps (COMP_PROPS no render-comp) — TTM e EST passam a sua citação.
          Duração auto pela extensão da frase (digitação + revelar autor + segurar + fade). */}
      <Composition
        id="TypewriterQuote"
        component={TypewriterQuote}
        fps={30}
        width={1920}
        height={1080}
        durationInFrames={240}
        defaultProps={{ quote: "Be silent for the most part, or say only what is necessary, and in few words.", author: "Epictetus", cps: 20 }}
        calculateMetadata={({ props }) => {
          const cps = props.cps || 20;
          const typeFrames = ((props.quote?.length || 60) / cps) * 30;
          return { durationInFrames: Math.ceil(typeFrames + 30 * 3.2) };
        }}
      />
      {/* Antes/depois: pacote de máscaras de edição cinematográficas sobre footage de stock */}
      <Composition id="EditMaskDemo" component={EditMaskDemo} durationInFrames={210} fps={30} width={1920} height={1080} />

      {/* ACERVO VidMator (ref. Harley/VidRush) — dado grande typewriter c/ zoom-out + glow */}
      <Composition id="StatReveal" component={StatReveal} durationInFrames={120} fps={30} width={1920} height={1080} />
      {/* ACERVO VidMator — foto antiga P&B angulada com zoom + leve rotação */}
      <Composition id="VintageAngled" component={VintageAngled} durationInFrames={105} fps={30} width={1920} height={1080} />
      {/* CTA de produto: foto + oferta tempo limitado (1º comentário) + QR + fundo exercício */}
      <Composition id="ProductCTAMock" component={ProductCTAMock} durationInFrames={180} fps={30} width={1920} height={1080} />

      {/* Card de pessoa histórica (retrato PD recortado + nome) */}
      <Composition id="PersonCard" component={PersonCard} durationInFrames={120} fps={30} width={1920} height={1080}
        defaultProps={{ nome: "Charles Darwin", imagem_rel: "test/people/darwin.png", subtitulo: "Naturalista · 1809–1882", fundo: "claro" as const }} />
      <Composition id="PersonCardDark" component={PersonCard} durationInFrames={120} fps={30} width={1920} height={1080}
        defaultProps={{ nome: "Charles Darwin", imagem_rel: "test/people/darwin.png", subtitulo: "Naturalista · 1809–1882", fundo: "escuro" as const }} />

      {/* CTA original (1080p ProRes c/ alpha) — uso real no engine.py */}
      <Composition
        id="CtaCard"
        component={CtaCard}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        schema={ctaCardSchema}
        defaultProps={{
          titulo: "Get the FREE Ebook",
          subtitulo: "Tap the link in description",
          accentColor: "#3ddc97",
        }}
      />

      {/* Reel: todas as 54 animações do acervo em sequência (preview) */}
      <Composition id="GalleryReel" component={GalleryReel} durationInFrames={REEL_FRAMES} fps={30} width={1920} height={1080} />

      {/* ===== ALMOXARIFADO TEXTO — preview por variante ===== */}
      <Composition id="TextoPreview" component={TextoPreview} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Texto01_Typewriter", text: "The engine started on the first try", kicker: "Durability", accent: "#f59e0b" }} />
      <Composition id="GraficoPreview" component={GraficoPreview} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Graf01_CounterGlow", title: "Units Produced", kicker: "Production", accent: "#f59e0b", labels: [], values: [18], suffix: "M" }} />
      <Composition id="ImagemPreview" component={ImagemPreview} durationInFrames={165} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Img01_KenBurnsCine", images: [], captions: [], title: "", kicker: "", accent: "#f59e0b" }} />
      <Composition id="SocialPreview" component={SocialPreview} durationInFrames={165} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Soc01_InstagramDM", autor: "", handle: "", titulo: "", texto: "", grifo: "", imagem: "", curtidas: 1000, kicker: "", accent: "#f59e0b" }} />
      <Composition id="FontePrancha" component={FontePrancha} durationInFrames={1} fps={30} width={1920} height={1080} />
      <Composition id="MapaPreview" component={MapaPreview} durationInFrames={165} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Map01_CountryFocus", paises: [], pontos: [], valores: [], titulo: "", kicker: "", accent: "#f59e0b" }} />
      <Composition id="TextoOverlayPreview" component={TextoOverlayPreview} durationInFrames={150} fps={30} width={1920} height={1080}
        defaultProps={{ variante: "Ovl01_ChapterBig", bg: "", text: "The engine started on the first try", kicker: "Chapter 02", accent: "#f59e0b" }} />

      {/* ===== MONTADOR (Stage 4) — renderiza jobs/<nome>/montagem.json ===== */}
      <Composition
        id="Montagem"
        component={Montagem}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ job: "hilux_mont", mont: null }}
        calculateMetadata={async ({ props }) => {
          if (props.mont) {
            return { durationInFrames: Math.ceil(props.mont.dur_s * 30), props };
          }
          const res = await fetch(staticFile(`jobs/${props.job}/montagem.json`));
          const mont = await res.json();
          return { durationInFrames: Math.ceil(mont.dur_s * 30), props: { ...props, mont } };
        }}
      />

      {/* ===== MONTADOR v5 (isolado — NÃO toca a Montagem v1-v4) ===== */}
      <Composition
        id="Montagem5"
        component={Montagem5}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ job: "hilux_mont", mont: null }}
        calculateMetadata={async ({ props }) => {
          if (props.mont) {
            return { durationInFrames: Math.ceil(props.mont.dur_s * 30), props };
          }
          const res = await fetch(staticFile(`jobs/${props.job}/montagem.json`));
          const mont = await res.json();
          return { durationInFrames: Math.ceil(mont.dur_s * 30), props: { ...props, mont } };
        }}
      />

      {/* ===== MÁSCARAS / CONTAINERS — StandardClip & montagem ===== */}
      {/* Frame + grid em perspectiva; 5 sub-clipes de 1–2s em corte seco (5×45f=225) */}
      <Composition id="FramedGridMontage" component={FramedGridMontage} durationInFrames={225} fps={30} width={1920} height={1080} />

      {/* ===== ACERVO VidMator — 54 templates (2026-07-16) ===== */}
      <Composition id="PercentageBarChart" component={PercentageBarChart} durationInFrames={110} fps={30} width={1920} height={1080} />
      <Composition id="PieChart" component={PieChart} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="LineChart" component={LineChart} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="GrowingBarChart" component={GrowingBarChart} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="BarChartComparison" component={BarChartComparison} durationInFrames={110} fps={30} width={1920} height={1080} />
      <Composition id="CirclePercent" component={CirclePercent} durationInFrames={110} fps={30} width={1920} height={1080} />
      <Composition id="NumberCountOverlay" component={NumberCountOverlay} durationInFrames={100} fps={30} width={1920} height={1080} />
      <Composition id="StockChart" component={StockChart} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="PriceCallOut" component={PriceCallOut} durationInFrames={100} fps={30} width={1920} height={1080} />
      <Composition id="ObjectDualStat" component={ObjectDualStat} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="PollSurveyBar" component={PollSurveyBar} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="OneWordCallout" component={OneWordCallout} durationInFrames={90} fps={30} width={1920} height={1080} />
      <Composition id="IconGrid" component={IconGrid} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="IconLabels" component={IconLabels} durationInFrames={110} fps={30} width={1920} height={1080} />
      <Composition id="CircleHighlight" component={CircleHighlight} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="BulletPointOverlay" component={BulletPointOverlay} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="MultiCountryOutline" component={MultiCountryOutline} durationInFrames={150} fps={30} width={1920} height={1080} />
      <Composition id="SatelliteDrawPath" component={SatelliteDrawPath} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="MapRoute" component={MapRoute} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="SatelliteLocationPin" component={SatelliteLocationPin} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="RegionLocationText" component={RegionLocationText} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="CountryCharacterMap" component={CountryCharacterMap} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="SentenceHighlight" component={SentenceHighlight} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="TextReveal" component={TextReveal} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="TitleDescription" component={TitleDescription} durationInFrames={100} fps={30} width={1920} height={1080} />
      <Composition id="QuoteCard" component={QuoteCard} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="ChapterTitle" component={ChapterTitle} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="DisplayText" component={DisplayText} durationInFrames={90} fps={30} width={1920} height={1080} />
      <Composition id="DateLocationOverlay" component={DateLocationOverlay} durationInFrames={90} fps={30} width={1920} height={1080} />
      <Composition id="CaptionTextOverlay" component={CaptionTextOverlay} durationInFrames={90} fps={30} width={1920} height={1080} />
      <Composition id="DualImpactSentence" component={DualImpactSentence} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="SingleSentenceTextSlide" component={SingleSentenceTextSlide} durationInFrames={100} fps={30} width={1920} height={1080} />
      <Composition id="CharacterCard" component={CharacterCard} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="CharacterKeyword" component={CharacterKeyword} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="ObjectTitle" component={ObjectTitle} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="NodeHierarchy" component={NodeHierarchy} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="SubjectTitleCard" component={SubjectTitleCard} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="DetectiveBoard" component={DetectiveBoard} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="InstagramConversation" component={InstagramConversation} durationInFrames={150} fps={30} width={1920} height={1080} />
      <Composition id="TwoImageComparison" component={TwoImageComparison} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="ThreeImageReveal" component={ThreeImageReveal} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="FourImageSlideshow" component={FourImageSlideshow} durationInFrames={160} fps={30} width={1920} height={1080} />
      <Composition id="MultiImageCutText" component={MultiImageCutText} durationInFrames={160} fps={30} width={1920} height={1080} />
      <Composition id="DualImageOnGrid" component={DualImageOnGrid} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="SplitScreenComparison" component={SplitScreenComparison} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="FourImageCaptionGrid" component={FourImageCaptionGrid} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="FiveTextListicle" component={FiveTextListicle} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="BeforeAfterArrow" component={BeforeAfterArrow} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="ImageTextAnnotation" component={ImageTextAnnotation} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="WebsiteScreenshotReveal" component={WebsiteScreenshotReveal} durationInFrames={140} fps={30} width={1920} height={1080} />
      <Composition id="ArticleNewsCard" component={ArticleNewsCard} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="LogoFlagGrid" component={LogoFlagGrid} durationInFrames={120} fps={30} width={1920} height={1080} />
      <Composition id="ImageCallout" component={ImageCallout} durationInFrames={130} fps={30} width={1920} height={1080} />
      <Composition id="PaperMovingTransparentObject" component={PaperMovingTransparentObject} durationInFrames={130} fps={30} width={1920} height={1080} />
    </>
  );
};
