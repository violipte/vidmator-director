// ALMOXARIFADO TEXTO-OVERLAY — 10 MP4s sobre footage real (auditoria). Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acov");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_texto_overlay";
mkdirSync(OUT, { recursive: true });

// fundo: primeiro vídeo stock T1 do job hilux (footage real atrás do overlay)
const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const bgBeat = mont.beats.find((b) => b.src && b.src.endsWith(".mp4") && b.tier === 1);
const bg = bgBeat ? bgBeat.src : "";
console.log("bg:", bg);

const CASOS = [
  ["Ovl01_ChapterBig", "Relentless Continuity", "Chapter 02"],
  ["Ovl02_SubchapterLine", "The N70 Generation", "Evolution"],
  ["Ovl03_LowerThird", "Ross Ice Shelf, Antarctica", "Expedition 2023"],
  ["Ovl04_FootnotePill", "WFP fleet logs, Horn of Africa 2019", "Source"],
  ["Ovl05_CornerTag", "1986", "Archive"],
  ["Ovl06_CenterPunch", "Unkillable", "The Verdict"],
  ["Ovl07_QuoteAttribution", "The trucks ran on low-grade fuel and never stopped", "Col. Mahamat Abdel-Kader"],
  ["Ovl08_SideNote", "The ladder frame uses ASTM A572 high-strength steel across all generations", "Engineering note"],
  ["Ovl09_TickerCaption", "Hilux maintains 92% operational uptime across UN humanitarian fleets", "Data"],
  ["Ovl10_NumberBadge", "Global parts availability in 180 markets", "#3"],
];

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acov") });
for (const [v, text, kicker] of CASOS) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, bg, text, kicker, accent: "#f59e0b" };
  const comp = await selectComposition({ serveUrl, id: "TextoOverlayPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_OVERLAY_DONE");
