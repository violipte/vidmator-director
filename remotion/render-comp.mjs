// Render programático de uma composição estática (galeria/demo) -> mp4 h264.
// Ignora o remotion.config (que seta ProRes p/ o CtaCard). Uso: node render-comp.mjs <CompId> <out.mp4>
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, readFileSync, existsSync } from "fs";

const TMP_F = resolve("_tmp");
mkdirSync(TMP_F, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP_F;
// PRUNE _tmp: Remotion não limpa temp de renders mortos (chegou a 118GB em 2026-07-03).
// Remove itens >3h no start — seguro: o lock do vidmator garante 1 render Remotion por vez.
try {
  const { readdirSync, statSync, rmSync } = await import("fs");
  const cut = Date.now() - 3 * 3600 * 1000;
  for (const e of readdirSync(TMP_F)) {
    const p = resolve(TMP_F, e);
    try { if (statSync(p).mtimeMs < cut) rmSync(p, { recursive: true, force: true }); } catch {}
  }
} catch {}

const ID = process.argv[2] || "PresentationGallery";
const OUT = resolve("out", process.argv[3] || `${ID}.mp4`);

// props opcionais p/ composições parametrizadas (ex: TypewriterQuote): COMP_PROPS = JSON inline OU caminho de arquivo .json
let inputProps = {};
const cp = process.env.COMP_PROPS;
if (cp) {
  try { inputProps = JSON.parse(cp.trim().startsWith("{") ? cp : readFileSync(cp, "utf8")); }
  catch (e) { console.error("COMP_PROPS inválido:", e.message); process.exit(1); }
  console.log("  inputProps:", JSON.stringify(inputProps).slice(0, 120));
}

console.log(`=== Bundle + render ${ID} ===`);
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle") });
const comp = await selectComposition({ serveUrl, id: ID, inputProps });
console.log(`  ${comp.durationInFrames} frames @ ${comp.fps}fps`);
await renderMedia({
  composition: comp, serveUrl, codec: "h264", outputLocation: OUT, inputProps,
  pixelFormat: "yuv420p", crf: 20, concurrency: 8, imageFormat: "jpeg", jpegQuality: 92,
  chromiumOptions: { gl: "angle" },
  onProgress: ({ progress }) => { if (Math.round(progress * 100) % 20 === 0) process.stdout.write(`\r  ${Math.round(progress * 100)}%`); },
});
console.log(`\n=== DONE -> ${OUT} ===`);
