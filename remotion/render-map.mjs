import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";

const OUT = resolve("out", "map_poc.mp4");

console.log("=== Bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts") });

console.log("=== Select composition ===");
const comp = await selectComposition({ serveUrl, id: "MapPoc", inputProps: {} });
console.log(`  duração: ${(comp.durationInFrames / comp.fps).toFixed(1)}s (${comp.durationInFrames} frames @ ${comp.fps}fps)`);

console.log("=== Render ===");
const t0 = Date.now();
await renderMedia({
  composition: comp,
  serveUrl,
  codec: "h264",
  outputLocation: OUT,
  pixelFormat: "yuv420p",
  crf: 18,
  onProgress: ({ progress }) => {
    if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`\r  ${Math.round(progress * 100)}%`);
  },
});
console.log(`\n=== DONE === ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}`);
