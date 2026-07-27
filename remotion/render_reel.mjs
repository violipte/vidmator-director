import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync } from "fs";

const BUNDLE = resolve("_bundle_reel");
const TMP = resolve("_tmp_reel");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

console.log("=== bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
const comp = await selectComposition({ serveUrl, id: "GalleryReel", inputProps: {} });
console.log(`reel: ${(comp.durationInFrames / 30).toFixed(0)}s (${comp.durationInFrames} frames)`);

await renderMedia({
  composition: comp, serveUrl, codec: "h264",
  outputLocation: resolve("out/acervo_reel.mp4"), inputProps: {},
  pixelFormat: "yuv420p", crf: 22, concurrency: 10, scale: 0.6,
  imageFormat: "jpeg", jpegQuality: 88,
  chromiumOptions: { gl: "angle" },
  offthreadVideoCacheSizeInBytes: 1024 * 1024 * 1024,
  onProgress: ({ progress }) => {
    if (Math.round(progress * 100) % 5 === 0) process.stdout.write(`\r${Math.round(progress * 100)}%`);
  },
});
console.log("\n=== REEL DONE === out/acervo_reel.mp4");
