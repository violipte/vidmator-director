import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { readFileSync } from "fs";
import { resolve } from "path";

const timeline = JSON.parse(readFileSync(resolve("timeline_render.json"), "utf-8"));
const OUT = resolve("out", "broll_slice.mp4");
const FROM = Number(process.argv[2] ?? 0);
const TO = Number(process.argv[3] ?? 900); // default 0-30s @30fps

console.log("=== Bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts") });

console.log("=== Select composition ===");
const comp = await selectComposition({ serveUrl, id: "BrollTest", inputProps: { timeline } });

console.log(`=== Render frames ${FROM}-${TO} ===`);
const t0 = Date.now();
await renderMedia({
  composition: comp,
  serveUrl,
  codec: "h264",
  outputLocation: OUT,
  inputProps: { timeline },
  pixelFormat: "yuv420p",
  crf: 20,
  frameRange: [FROM, TO],
  onProgress: ({ progress }) => {
    if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`\r  ${Math.round(progress * 100)}%`);
  },
});
console.log(`\n=== DONE === ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}`);
