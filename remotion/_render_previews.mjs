// PREVIEWS POR ANIMAÇÃO (workflow Piter): 1 MP4 por beat de animação do montagem.json.
// Resumível (pula os já feitos). Saída: banco-videos/_job_hilux/previews/b###__Componente.mp4
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, readFileSync, existsSync } from "fs";

const BUNDLE = resolve("_bundle_prev");
const TMP = resolve("_tmp_prev");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_job_hilux/previews";
mkdirSync(OUT, { recursive: true });

const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const anims = mont.beats.filter((b) => b.tipo === "animacao");
console.log(`animações: ${anims.length}`);

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: BUNDLE });
const comp = await selectComposition({ serveUrl, id: "Montagem", inputProps: { job: "hilux_mont", mont } });

let feitos = 0;
for (const b of anims) {
  const nome = `b${String(b.i).padStart(3, "0")}__${b.componente || "X"}.mp4`;
  const dest = `${OUT}/${nome}`;
  if (existsSync(dest)) { feitos++; continue; }
  const f0 = Math.round(b.t_ini * 30);
  const f1 = Math.max(f0 + 1, Math.round(b.t_fim * 30) - 1);
  await renderMedia({
    composition: comp, serveUrl, codec: "h264", outputLocation: dest,
    inputProps: { job: "hilux_mont", mont }, pixelFormat: "yuv420p", crf: 21,
    concurrency: 10, frameRange: [f0, f1], imageFormat: "jpeg", jpegQuality: 88,
    chromiumOptions: { gl: "angle" }, muted: true,
  });
  feitos++;
  console.log(`${feitos}/${anims.length} ${nome}`);
}
console.log("PREVIEWS_DONE");
