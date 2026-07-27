// Demos: overlay sobre IMAGEM + variações de dim (escurecimento do fundo).
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acov2");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_texto_overlay";

const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const vid = mont.beats.find((b) => b.src && b.src.endsWith(".mp4") && b.tier === 1)?.src || "";
const img = mont.beats.find((b) => b.src && /\.(jpg|png)$/i.test(b.src))?.src || "";
console.log("vid:", vid, "| img:", img);

const DEMOS = [
  ["_demo_ChapterBig_sobre_IMAGEM", { variante: "Ovl01_ChapterBig", bg: img, dim: 0, text: "Relentless Continuity", kicker: "Chapter 02" }],
  ["_demo_CenterPunch_dim035", { variante: "Ovl06_CenterPunch", bg: vid, dim: 0.35, text: "Unkillable", kicker: "The Verdict" }],
  ["_demo_SideNote_dim055", { variante: "Ovl08_SideNote", bg: vid, dim: 0.55, text: "The ladder frame uses ASTM A572 high-strength steel across all generations", kicker: "Engineering note" }],
];

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acov2") });
for (const [nome, props] of DEMOS) {
  const inputProps = { accent: "#f59e0b", ...props };
  const comp = await selectComposition({ serveUrl, id: "TextoOverlayPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: `${OUT}/${nome}.mp4`, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", nome);
}
console.log("DEMOS_DONE");
