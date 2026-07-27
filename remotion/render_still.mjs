import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync } from "fs";

const BUNDLE = resolve("_bundle_preview");
const TMP = resolve("_tmp_preview");
mkdirSync(TMP, { recursive: true });
mkdirSync(resolve("out"), { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;

console.log("=== bundle ===");
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });

const jobs = [
  { id: "StatReveal", frame: 45, out: "out/_preview_statreveal.png", props: {} },
  { id: "VintageAngled", frame: 60, out: "out/_preview_vintage.png", props: { src: "jobs/motos2/clips/moto0.jpg", dir: "out" } },
];
for (const j of jobs) {
  const comp = await selectComposition({ serveUrl, id: j.id, inputProps: j.props });
  await renderStill({ composition: comp, serveUrl, output: resolve(j.out), frame: j.frame, inputProps: j.props, chromiumOptions: { gl: "angle" } });
  console.log("OK", j.id, "->", j.out);
}
console.log("=== STILLS DONE ===");
