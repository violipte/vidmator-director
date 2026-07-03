import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
const id = process.argv[2];
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts") });
const comp = await selectComposition({ serveUrl, id, inputProps: {} });
await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: resolve("out", id + ".mp4"),
  pixelFormat: "yuv420p", crf: 18, onProgress: ({progress}) => { if (Math.round(progress*100)%20===0) process.stdout.write(`\r${id} ${Math.round(progress*100)}%`); } });
console.log(`\n${id} DONE`);
