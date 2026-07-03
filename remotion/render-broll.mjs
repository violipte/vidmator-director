import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { readFileSync, mkdirSync, existsSync, writeFileSync, renameSync, rmSync } from "fs";
import { resolve } from "path";
import { execSync } from "child_process";
import os from "os";

// TEMP do Remotion FORA do C: (bundles ~2,45GB + frames enchiam o C: e travavam tudo).
// TMP/bundle vão pra F:; o bundle usa um outDir FIXO (sobrescreve -> não acumula 56 pastas).
const TMP_F = process.env.REMOTION_TMP || resolve("_tmp");
const BUNDLE_DIR = process.env.REMOTION_BUNDLE || resolve("_bundle");
mkdirSync(TMP_F, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP_F;
// PRUNE _tmp: Remotion não limpa temp de renders mortos (chegou a 118GB em 2026-07-03).
// Remove itens >3h no start — seguro: o lock do vidmator garante 1 render Remotion por vez.
try {
  const { readdirSync, statSync } = await import("fs");
  const cut = Date.now() - 3 * 3600 * 1000;
  for (const e of readdirSync(TMP_F)) {
    const p = resolve(TMP_F, e);
    try { if (statSync(p).mtimeMs < cut) rmSync(p, { recursive: true, force: true }); } catch {}
  }
} catch {}

// Config dirigível por env (tuning sem editar arquivo):
//   RENDER_CONCURRENCY=10 RENDER_GL=none node render-broll.mjs
// Default vencedor do benchmark: GPU (angle) + concurrency 14 (~34% mais rápido, estável).
// Concurrency alto demais (ex.: 31) satura a GPU e causa EncodingError -> cap em 14.
const CONCURRENCY = Number(process.env.RENDER_CONCURRENCY) || Math.max(4, Math.min(14, os.cpus().length - 2));
const GL_RAW = process.env.RENDER_GL ?? "angle";  // GPU/D3D no Windows; RENDER_GL=none p/ desligar
const GL = GL_RAW && GL_RAW !== "none" ? GL_RAW : null;

// Por-job: RENDER_TIMELINE (json de entrada) e RENDER_OUT (mp4 de saída) p/ produção em lote/paralelo.
const TL_IN = process.env.RENDER_TIMELINE || "timeline_render.json";
const timeline = JSON.parse(readFileSync(resolve(TL_IN), "utf-8"));
const OUT = resolve("out", process.env.RENDER_OUT || "broll_test.mp4");

console.log(`=== Bundle (outDir=${BUNDLE_DIR}) ===`);
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE_DIR });

console.log("=== Select composition ===");
const comp = await selectComposition({
  serveUrl,
  id: "BrollTest",
  inputProps: { timeline },
});
console.log(`  duração: ${(comp.durationInFrames / comp.fps).toFixed(1)}s (${comp.durationInFrames} frames @ ${comp.fps}fps)`);

// RENDER_CHUNKS=N -> renderiza em N pedaços resumíveis (cada um com seu FFmpeg curto). À prova de
// queda de energia E do FFmpeg 0xC0000142 (falha de spawn sob pressão): re-rodar pula chunks prontos
// e retoma só o que falta. RENDER_CHUNKS ausente/1 = render único (comportamento antigo).
const CHUNKS = Math.max(1, Number(process.env.RENDER_CHUNKS) || 1);
const baseSettings = {
  composition: comp, serveUrl, codec: "h264", inputProps: { timeline },
  pixelFormat: "yuv420p", crf: 20, concurrency: CONCURRENCY,
  imageFormat: "jpeg", jpegQuality: 92,
  offthreadVideoCacheSizeInBytes: 2 * 1024 * 1024 * 1024,
  ...(GL ? { chromiumOptions: { gl: GL } } : {}),
};
const t0 = Date.now();

const RANGE = process.env.RENDER_RANGE;  // "0-360" -> renderiza só esse trecho (teste rápido)
if (CHUNKS <= 1) {
  const fr = RANGE ? RANGE.split("-").map(Number) : undefined;
  console.log(`=== Render (concurrency=${CONCURRENCY}, gl=${GL || "default"}, jpeg${fr ? `, range ${RANGE}` : ""}) ===`);
  await renderMedia({
    ...baseSettings, outputLocation: OUT, ...(fr ? { frameRange: fr } : {}),
    onProgress: ({ progress }) => {
      if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`\r  ${Math.round(progress * 100)}%`);
    },
  });
} else {
  const total = comp.durationInFrames;
  const size = Math.ceil(total / CHUNKS);
  const chunkDir = resolve("out", "_chunks");
  mkdirSync(chunkDir, { recursive: true });
  const base = (process.env.RENDER_OUT || "broll_test.mp4").replace(/\.mp4$/i, "");
  console.log(`=== Render em ${CHUNKS} chunks (concurrency=${CONCURRENCY}, gl=${GL || "default"}) ===`);
  const parts = [];
  for (let k = 0; k < CHUNKS; k++) {
    const a = k * size, b = Math.min((k + 1) * size - 1, total - 1);
    if (a > b) break;
    const part = resolve(chunkDir, `${base}.part${String(k).padStart(2, "0")}.mp4`);
    parts.push(part);
    if (existsSync(part)) { console.log(`  chunk ${k + 1}/${CHUNKS} (frames ${a}-${b}) já pronto -> pula`); continue; }
    const tmp = part + ".tmp.mp4";   // só vira final quando COMPLETO (resume seguro contra parcial corrompido)
    process.stdout.write(`  chunk ${k + 1}/${CHUNKS} (frames ${a}-${b}): `);
    await renderMedia({
      ...baseSettings, outputLocation: tmp, frameRange: [a, b],
      onProgress: ({ progress }) => {
        if (Math.round(progress * 100) % 20 === 0) process.stdout.write(`${Math.round(progress * 100)}% `);
      },
    });
    renameSync(tmp, part);
    process.stdout.write("ok\n");
  }
  // concatena (FFmpeg externo, -c copy = lossless e rápido; todos os chunks têm os mesmos params)
  console.log("=== Concat dos chunks ===");
  const listPath = resolve(chunkDir, `${base}.list.txt`);
  writeFileSync(listPath, parts.map((p) => `file '${p.replace(/\\/g, "/")}'`).join("\n"));
  execSync(`ffmpeg -y -f concat -safe 0 -i "${listPath}" -c copy "${OUT}"`, { stdio: "inherit" });
  // limpa chunks só após concat OK
  for (const p of parts) rmSync(p, { force: true });
  rmSync(listPath, { force: true });
}
console.log(`\n=== DONE === ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${OUT}`);
