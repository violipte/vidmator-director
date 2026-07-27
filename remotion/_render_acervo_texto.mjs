// ALMOXARIFADO TEXTO — 10 MP4s individuais (mesmo texto p/ comparação justa). Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync } from "fs";

const TMP = resolve("_tmp_actx");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_texto";
mkdirSync(OUT, { recursive: true });

const VARIANTES = [
  "Texto01_Typewriter", "Texto02_HighlightSweep", "Texto03_WordPop", "Texto04_EditorialSerif",
  "Texto05_BoxedKicker", "Texto06_SplitBar", "Texto07_StampImpact", "Texto08_GradientGlow",
  "Texto09_UnderlineDraw", "Texto10_LetterCascade",
];
const AMOSTRA = { text: "The engine started on the first try", kicker: "Durability", accent: "#f59e0b" };

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_actx") });
for (const v of VARIANTES) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, ...AMOSTRA };
  const comp = await selectComposition({ serveUrl, id: "TextoPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_TEXTO_DONE");
