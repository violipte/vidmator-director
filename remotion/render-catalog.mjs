/**
 * Renderiza todas as 15 Compositions do catálogo em MP4 H.264 1280×720.
 * Output: ./out/*.mp4
 *
 * Override config: NÃO usa ProRes 4444 (alpha). Usa H.264 yuv420p — leve pro browser.
 */
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { mkdirSync, existsSync } from "fs";
import { resolve } from "path";

const OUT_DIR = resolve("out");
mkdirSync(OUT_DIR, { recursive: true });

const CATALOG_IDS = [
  "01-CrossfadeTransition",
  "02-SlideHorizontalTransition",
  "03-WhipPanTransition",
  "04-SmoothZoomTransition",
  "05-LightRays",
  "06-ParticlesDrift",
  "07-StarsDrifting",
  "08-AuroraGlow",
  "09-LightLeak",
  "10-CtaCardSide",
  "11-CtaBannerSlim",
  "12-CtaPopupCenter",
  "13-WordByWordReveal",
  "14-SubscribeBellPulse",
  "15-SubscribeMinimal",
];

console.log("=== Bundling Remotion project ===");
const t0 = Date.now();
const serveUrl = await bundle({
  entryPoint: resolve("src/index.ts"),
  webpackOverride: (cfg) => cfg,
});
console.log(`Bundled in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
console.log();

let success = 0, failed = 0;
const startBatch = Date.now();

for (const id of CATALOG_IDS) {
  const out = resolve(OUT_DIR, `${id}.mp4`);
  if (existsSync(out)) {
    console.log(`SKIP ${id} (já existe)`);
    success++;
    continue;
  }
  const t1 = Date.now();
  process.stdout.write(`Rendering ${id}...`);
  try {
    const comp = await selectComposition({ serveUrl, id, inputProps: {} });
    await renderMedia({
      composition: comp,
      serveUrl,
      codec: "h264",
      outputLocation: out,
      pixelFormat: "yuv420p",
      imageFormat: "png",
      crf: 23,
      inputProps: {},
      muted: true,
      enforceAudioTrack: false,
    });
    const dt = ((Date.now() - t1) / 1000).toFixed(1);
    console.log(` OK (${dt}s)`);
    success++;
  } catch (e) {
    console.log(` FAIL: ${e.message}`);
    failed++;
  }
}

const total = ((Date.now() - startBatch) / 1000).toFixed(1);
console.log();
console.log(`=== DONE === ${success} OK / ${failed} FAIL / total ${total}s`);
process.exit(failed > 0 ? 1 : 0);
