import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync } from "fs";

const BUNDLE = resolve("_bundle_audit");
const TMP = resolve("_tmp_audit");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out/_gallery"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

// 48 animações NÃO-mapa (mapas ficam pra depois)
const IDS = [
  // Gráficos & Dados
  "PercentageBarChart","PieChart","LineChart","GrowingBarChart","BarChartComparison","CirclePercent","NumberCountOverlay","StockChart",
  // Stats & Callouts
  "PriceCallOut","ObjectDualStat","PollSurveyBar","OneWordCallout","IconGrid","IconLabels","CircleHighlight","BulletPointOverlay",
  // Texto
  "SentenceHighlight","TextReveal","TitleDescription","QuoteCard","ChapterTitle","DisplayText","DateLocationOverlay","CaptionTextOverlay","DualImpactSentence","SingleSentenceTextSlide",
  // Pessoas & Objetos
  "CharacterCard","CharacterKeyword","ObjectTitle","NodeHierarchy","SubjectTitleCard","DetectiveBoard","InstagramConversation",
  // Imagens & Comparação
  "TwoImageComparison","ThreeImageReveal","FourImageSlideshow","MultiImageCutText","DualImageOnGrid","SplitScreenComparison","FourImageCaptionGrid","FiveTextListicle","BeforeAfterArrow","ImageTextAnnotation","WebsiteScreenshotReveal","ArticleNewsCard","LogoFlagGrid","ImageCallout","PaperMovingTransparentObject",
];

console.log("=== bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
let ok = 0, fail = 0;
for (const id of IDS) {
  try {
    const comp = await selectComposition({ serveUrl, id, inputProps: {} });
    const frame = Math.max(1, Math.floor(comp.durationInFrames * 0.82));
    await renderStill({ composition: comp, serveUrl, output: resolve(`out/_gallery/${id}.png`), frame, inputProps: {}, chromiumOptions: { gl: "angle" }, scale: 0.66 });
    ok++; process.stdout.write(".");
  } catch (e) {
    fail++; console.log("\nFAIL", id, String(e).slice(0, 120));
  }
}
console.log(`\n=== AUDIT STILLS DONE === ok=${ok} fail=${fail}`);
