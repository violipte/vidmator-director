// ALMOXARIFADO IMAGEM — 20 MP4s com fotos REAIS do job hilux. Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acim");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_imagem";
mkdirSync(OUT, { recursive: true });

const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const fotos = mont.beats.filter((b) => b.src && /\.(jpg|png)$/i.test(b.src) && !b.src.includes("GEN")).map((b) => b.src);
const gen = mont.beats.filter((b) => b.src && b.src.includes("GEN")).map((b) => b.src);
const IMS = [...fotos, ...gen];
console.log("fotos disponiveis:", IMS.length);
const pick = (n, off = 0) => Array.from({ length: n }, (_, i) => IMS[(off + i) % IMS.length]);

const CASOS = [
  ["Img01_KenBurnsCine", { images: pick(1, 0), title: "The Legend Begins" }],
  ["Img02_PolaroidDrop", { images: pick(1, 1), captions: ["Queensland, 1994"] }],
  ["Img03_FramedGridPan", { images: pick(1, 2), captions: ["Archive footage"] }],
  ["Img04_SplitSlide", { images: pick(2, 3), captions: ["Factory build", "Field service"] }],
  ["Img05_BeforeAfterWipe", { images: pick(2, 5), captions: ["Before", "After"] }],
  ["Img06_StackReveal", { images: pick(3, 7) }],
  ["Img07_FilmstripSlide", { images: pick(4, 10) }],
  ["Img08_GridPop", { images: pick(4, 14), captions: ["Engine", "Chassis", "Suspension", "Drivetrain"] }],
  ["Img09_PaperTear", { images: pick(1, 4), captions: ["Service manual, page 112"], kicker: "Evidence" }],
  ["Img10_ParallaxDepth", { images: pick(1, 6), title: "Built to outlast everything", kicker: "Chapter 03" }],
  ["Img11_VintageAngled", { images: pick(1, 18), captions: ["Thailand plant, 1979"] }],
  ["Img12_SpotlightDetail", { images: pick(1, 20), captions: ["Reinforced frame rail"] }],
  ["Img13_MagnifierInspect", { images: pick(1, 22) }],
  ["Img14_TitleCutout", { images: pick(1, 24), title: "HILUX" }],
  ["Img15_CorkBoardPin", { images: pick(2, 26), captions: ["Exhibit A", "Exhibit B"] }],
  ["Img16_ZoomOutReveal", { images: pick(1, 28), captions: ["The whole story"] }],
  ["Img17_DiagonalDuo", { images: pick(2, 30), captions: ["Factory", "Field"] }],
  ["Img18_PhotoStatBadge", { images: pick(1, 32), title: "650K", kicker: "Kilometers", captions: ["on a single truck, no overhaul"] }],
  ["Img19_NewsClipping", { images: pick(1, 34), title: "The truck that would not die", kicker: "The Motor Herald", captions: ["Engineers confirmed the engine started on the first try."] }],
  ["Img20_TripleCarousel", { images: pick(3, 36), captions: ["Generation N70"] }],
];

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acim") });
for (const [v, props] of CASOS) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, accent: "#f59e0b", ...props };
  const comp = await selectComposition({ serveUrl, id: "ImagemPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_IMAGEM_DONE");
