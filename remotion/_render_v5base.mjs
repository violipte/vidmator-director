// Render do job TENIS (Stage 4). Uso: node _render_tenis.mjs [ini_s] [fim_s]
// Isolado por JOB: bundle/tmp ABSOLUTOS próprios.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, readFileSync } from "fs";

const BUNDLE = resolve("_bundle_v5base");
const TMP = resolve("_tmp_v5base");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out/_v5base"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

const mont = JSON.parse(readFileSync(resolve("public/jobs/v5base_mont/montagem.json"), "utf-8"));
const modoAudio = process.argv.includes("--audio");   // v5 F2: passada única de áudio (WAV)
const ini = process.argv[2] && process.argv[2] !== "--audio" ? parseFloat(process.argv[2]) : 0;
const fim = process.argv[3] && process.argv[3] !== "--audio" ? parseFloat(process.argv[3]) : mont.dur_s;
const frameRange = [Math.round(ini * 30), Math.min(Math.round(fim * 30) - 1, Math.ceil(mont.dur_s * 30) - 1)];
const out = modoAudio ? "out/_v5base/v5base_audio.wav"
  : ini === 0 && fim >= mont.dur_s ? "out/_v5base/v5base_full.mp4" : `out/_v5base/v5base_${ini}_${fim}.mp4`;

console.log(`=== bundle === ${modoAudio ? "AUDIO full" : `slice ${ini}-${fim}s frames ${frameRange}`}`);
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
const comp = await selectComposition({ serveUrl, id: "Montagem5", inputProps: { job: "v5base_mont", mont } });
console.log(`dur total: ${comp.durationInFrames}f`);

await renderMedia({
  composition: comp, serveUrl, codec: modoAudio ? "wav" : "h264",
  outputLocation: resolve(out), inputProps: { job: "v5base_mont", mont },
  ...(modoAudio ? {} : { pixelFormat: "yuv420p", crf: 20, frameRange }),
  concurrency: 14,
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
