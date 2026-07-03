import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";

const OUT = resolve("out", "doodles.mp4");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts") });
const comp = await selectComposition({ serveUrl, id: "DoodleGallery", inputProps: {} });
const t0 = Date.now();
await renderMedia({
  composition: comp, serveUrl, codec: "h264", outputLocation: OUT,
  pixelFormat: "yuv420p", crf: 18,
  onProgress: ({ progress }) => { if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`\r  ${Math.round(progress * 100)}%`); },
});
console.log(`\nDONE ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}`);
