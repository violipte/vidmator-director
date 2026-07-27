import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync } from "fs";

const BUNDLE = resolve("_bundle_gallery");
const TMP = resolve("_tmp_gallery");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out/_gallery"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

const IDS = [
  ["PercentageBarChart",110],["PieChart",130],["LineChart",130],["GrowingBarChart",120],
  ["BarChartComparison",110],["CirclePercent",110],["NumberCountOverlay",100],["StockChart",130],
  ["PriceCallOut",100],["ObjectDualStat",120],["PollSurveyBar",120],["OneWordCallout",90],
  ["IconGrid",130],["IconLabels",110],["CircleHighlight",130],["BulletPointOverlay",120],
  ["MultiCountryOutline",150],["SatelliteDrawPath",140],["MapRoute",140],["SatelliteLocationPin",130],
  ["RegionLocationText",130],["CountryCharacterMap",140],
  ["SentenceHighlight",140],["TextReveal",120],["TitleDescription",100],["QuoteCard",120],
  ["ChapterTitle",130],["DisplayText",90],["DateLocationOverlay",90],["CaptionTextOverlay",90],
  ["DualImpactSentence",130],["SingleSentenceTextSlide",100],
  ["CharacterCard",120],["CharacterKeyword",120],["ObjectTitle",120],["NodeHierarchy",130],
  ["SubjectTitleCard",120],["DetectiveBoard",140],["InstagramConversation",150],
  ["TwoImageComparison",130],["ThreeImageReveal",140],["FourImageSlideshow",160],["MultiImageCutText",160],
  ["DualImageOnGrid",120],["SplitScreenComparison",130],["FourImageCaptionGrid",120],["FiveTextListicle",130],
  ["BeforeAfterArrow",130],["ImageTextAnnotation",140],["WebsiteScreenshotReveal",140],["ArticleNewsCard",130],
  ["LogoFlagGrid",120],["ImageCallout",130],["PaperMovingTransparentObject",130],
];

console.log("=== bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
console.log("bundle ok");

let ok = 0; const fail = [];
for (const [id, dur] of IDS) {
  try {
    const comp = await selectComposition({ serveUrl, id, inputProps: {} });
    const frame = Math.max(1, Math.floor(dur * 0.72));
    await renderStill({ composition: comp, serveUrl, output: resolve(`out/_gallery/${id}.png`), frame, inputProps: {}, chromiumOptions: { gl: "angle" } });
    ok++; process.stdout.write(".");
  } catch (e) {
    fail.push(`${id}: ${String(e).replace(/\s+/g, " ").slice(0, 140)}`);
    process.stdout.write("X");
  }
}
console.log(`\nOK ${ok}/${IDS.length}`);
if (fail.length) { console.log("FALHAS:"); fail.forEach((f) => console.log("  - " + f)); }
console.log("=== GALLERY DONE ===");
