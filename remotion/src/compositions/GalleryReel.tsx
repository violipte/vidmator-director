import { AbsoluteFill, Sequence } from "remotion";
import { PercentageBarChart } from "./PercentageBarChart";
import { PieChart } from "./PieChart";
import { LineChart } from "./LineChart";
import { GrowingBarChart } from "./GrowingBarChart";
import { BarChartComparison } from "./BarChartComparison";
import { CirclePercent } from "./CirclePercent";
import { NumberCountOverlay } from "./NumberCountOverlay";
import { StockChart } from "./StockChart";
import { PriceCallOut } from "./PriceCallOut";
import { ObjectDualStat } from "./ObjectDualStat";
import { PollSurveyBar } from "./PollSurveyBar";
import { OneWordCallout } from "./OneWordCallout";
import { IconGrid } from "./IconGrid";
import { IconLabels } from "./IconLabels";
import { CircleHighlight } from "./CircleHighlight";
import { BulletPointOverlay } from "./BulletPointOverlay";
import { MultiCountryOutline } from "./MultiCountryOutline";
import { SatelliteDrawPath } from "./SatelliteDrawPath";
import { MapRoute } from "./MapRoute";
import { SatelliteLocationPin } from "./SatelliteLocationPin";
import { RegionLocationText } from "./RegionLocationText";
import { CountryCharacterMap } from "./CountryCharacterMap";
import { SentenceHighlight } from "./SentenceHighlight";
import { TextReveal } from "./TextReveal";
import { TitleDescription } from "./TitleDescription";
import { QuoteCard } from "./QuoteCard";
import { ChapterTitle } from "./ChapterTitle";
import { DisplayText } from "./DisplayText";
import { DateLocationOverlay } from "./DateLocationOverlay";
import { CaptionTextOverlay } from "./CaptionTextOverlay";
import { DualImpactSentence } from "./DualImpactSentence";
import { SingleSentenceTextSlide } from "./SingleSentenceTextSlide";
import { CharacterCard } from "./CharacterCard";
import { CharacterKeyword } from "./CharacterKeyword";
import { ObjectTitle } from "./ObjectTitle";
import { NodeHierarchy } from "./NodeHierarchy";
import { SubjectTitleCard } from "./SubjectTitleCard";
import { DetectiveBoard } from "./DetectiveBoard";
import { InstagramConversation } from "./InstagramConversation";
import { TwoImageComparison } from "./TwoImageComparison";
import { ThreeImageReveal } from "./ThreeImageReveal";
import { FourImageSlideshow } from "./FourImageSlideshow";
import { MultiImageCutText } from "./MultiImageCutText";
import { DualImageOnGrid } from "./DualImageOnGrid";
import { SplitScreenComparison } from "./SplitScreenComparison";
import { FourImageCaptionGrid } from "./FourImageCaptionGrid";
import { FiveTextListicle } from "./FiveTextListicle";
import { BeforeAfterArrow } from "./BeforeAfterArrow";
import { ImageTextAnnotation } from "./ImageTextAnnotation";
import { WebsiteScreenshotReveal } from "./WebsiteScreenshotReveal";
import { ArticleNewsCard } from "./ArticleNewsCard";
import { LogoFlagGrid } from "./LogoFlagGrid";
import { ImageCallout } from "./ImageCallout";
import { PaperMovingTransparentObject } from "./PaperMovingTransparentObject";

export const SLOT = 96; // 3.2s por animação

const ITEMS: { C: React.FC; name: string }[] = [
  { C: PercentageBarChart, name: "Percentage Bar Chart" }, { C: PieChart, name: "Pie Chart" },
  { C: LineChart, name: "Line Chart" }, { C: GrowingBarChart, name: "Growing Bar Chart" },
  { C: BarChartComparison, name: "Bar Chart Comparison" }, { C: CirclePercent, name: "Circle Percent" },
  { C: NumberCountOverlay, name: "Number Count" }, { C: StockChart, name: "Stock Chart" },
  { C: PriceCallOut, name: "Price Call Out" }, { C: ObjectDualStat, name: "Object Dual Stat" },
  { C: PollSurveyBar, name: "Poll / Survey Bar" }, { C: OneWordCallout, name: "One Word Callout" },
  { C: IconGrid, name: "Icon Grid" }, { C: IconLabels, name: "Icon Labels" },
  { C: CircleHighlight, name: "Circle Highlight" }, { C: BulletPointOverlay, name: "Bullet Points" },
  { C: MultiCountryOutline, name: "Multi Country Outline" }, { C: SatelliteDrawPath, name: "Satellite Draw Path" },
  { C: MapRoute, name: "Map Route" }, { C: SatelliteLocationPin, name: "Satellite Location Pin" },
  { C: RegionLocationText, name: "Region Location Text" }, { C: CountryCharacterMap, name: "Country + Character Map" },
  { C: SentenceHighlight, name: "Sentence Highlight" }, { C: TextReveal, name: "Text Reveal" },
  { C: TitleDescription, name: "Title + Description" }, { C: QuoteCard, name: "Quote Card" },
  { C: ChapterTitle, name: "Chapter Title" }, { C: DisplayText, name: "Display Text" },
  { C: DateLocationOverlay, name: "Date / Location Overlay" }, { C: CaptionTextOverlay, name: "Caption Overlay" },
  { C: DualImpactSentence, name: "Dual Impact Sentence" }, { C: SingleSentenceTextSlide, name: "Single Sentence Slide" },
  { C: CharacterCard, name: "Character Card" }, { C: CharacterKeyword, name: "Character + Keyword" },
  { C: ObjectTitle, name: "Object + Title" }, { C: NodeHierarchy, name: "Node Hierarchy" },
  { C: SubjectTitleCard, name: "Subject Title Card" }, { C: DetectiveBoard, name: "Detective Board" },
  { C: InstagramConversation, name: "Instagram Conversation" }, { C: TwoImageComparison, name: "Two Image Comparison" },
  { C: ThreeImageReveal, name: "Three Image Reveal" }, { C: FourImageSlideshow, name: "Four Image Slideshow" },
  { C: MultiImageCutText, name: "Multi Image Cut Text" }, { C: DualImageOnGrid, name: "Dual Image on Grid" },
  { C: SplitScreenComparison, name: "Split Screen Comparison" }, { C: FourImageCaptionGrid, name: "Four Image Caption Grid" },
  { C: FiveTextListicle, name: "Five Text Listicle" }, { C: BeforeAfterArrow, name: "Before / After Arrow" },
  { C: ImageTextAnnotation, name: "Image Text Annotation" }, { C: WebsiteScreenshotReveal, name: "Website Screenshot Reveal" },
  { C: ArticleNewsCard, name: "Article / News Card" }, { C: LogoFlagGrid, name: "Logo / Flag Grid" },
  { C: ImageCallout, name: "Image Callout" }, { C: PaperMovingTransparentObject, name: "Paper Moving Transparent Object" },
];

export const REEL_FRAMES = ITEMS.length * SLOT;

const NameTag: React.FC<{ name: string; i: number }> = ({ name, i }) => (
  <div style={{ position: "absolute", left: 44, bottom: 40, display: "flex", alignItems: "center", gap: 14,
    background: "rgba(0,0,0,0.72)", padding: "10px 22px", borderRadius: 10, backdropFilter: "blur(4px)" }}>
    <span style={{ color: "#f59e0b", fontFamily: "'Archivo Black','Impact',sans-serif", fontSize: 28 }}>{String(i + 1).padStart(2, "0")}</span>
    <span style={{ color: "#fff", fontFamily: "'Inter','Segoe UI',sans-serif", fontWeight: 700, fontSize: 32, letterSpacing: 0.5 }}>{name}</span>
  </div>
);

export const GalleryReel: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    {ITEMS.map((it, i) => {
      const C = it.C;
      return (
        <Sequence key={i} from={i * SLOT} durationInFrames={SLOT}>
          <C />
          <NameTag name={it.name} i={i} />
        </Sequence>
      );
    })}
  </AbsoluteFill>
);
