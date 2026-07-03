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
    </>
  );
};
