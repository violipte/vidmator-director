// Render do job TENIS (Stage 4). Uso: node _render_tenis.mjs [ini_s] [fim_s]
// Isolado por JOB: bundle/tmp ABSOLUTOS próprios.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, readFileSync } from "fs";

const BUNDLE = resolve("_bundle_estoico");
const TMP = resolve("_tmp_estoico");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out/_estoico"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

const mont = JSON.parse(readFileSync(resolve("public/jobs/estoico_mont/montagem.json"), "utf-8"));
const ini = process.argv[2] ? parseFloat(process.argv[2]) : 0;
const fim = process.argv[3] ? parseFloat(process.argv[3]) : mont.dur_s;
const frameRange = [Math.round(ini * 30), Math.min(Math.round(fim * 30) - 1, Math.ceil(mont.dur_s * 30) - 1)];
const out = ini === 0 && fim >= mont.dur_s ? "out/_estoico/estoico_full.mp4" : `out/_estoico/estoico_${ini}_${fim}.mp4`;

console.log(`=== bundle === slice ${ini}-${fim}s frames ${frameRange}`);
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
const comp = await selectComposition({ serveUrl, id: "Montagem", inputProps: { job: "estoico_mont", mont } });
console.log(`dur total: ${comp.durationInFrames}f`);

await renderMedia({
  composition: comp, serveUrl, codec: "h264",
  outputLocation: resolve(out), inputProps: { job: "estoico_mont", mont },
  pixelFormat: "yuv420p", crf: 20, concurrency: 14, frameRange,
  imageFormat: "jpeg", jpegQuality: 90,
  chromiumOptions: { gl: "angle" },
  offthreadVideoCacheSizeInBytes: 1024 * 1024 * 1024,
  timeoutInMilliseconds: 120000,
  onProgress: ({ progress }) => {
    const p = Math.round(progress * 100);
    if (p % 5 === 0) process.stdout.write(`\r${p}%`);
  },
});
console.log(`\n=== DONE === ${out}`);
