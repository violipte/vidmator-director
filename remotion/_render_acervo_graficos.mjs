// ALMOXARIFADO GRÁFICOS — 10 MP4s individuais com dados de exemplo por forma. Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acgr");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_graficos";
mkdirSync(OUT, { recursive: true });

const CASOS = [
  ["Graf01_CounterGlow", { title: "Units Produced", kicker: "Production", values: [18], suffix: "M" }],
  ["Graf02_Odometer", { title: "Kilometers on one truck", kicker: "Odometer", values: [650000], suffix: "" }],
  ["Graf03_DonutPercent", { title: "Fleet operational uptime", kicker: "Reliability", values: [92], suffix: "%" }],
  ["Graf04_GaugeMeter", { title: "Engine load tolerance", kicker: "Stress Test", values: [86], suffix: "%" }],
  ["Graf05_VersusBars", { title: "Annual Fleet Uptime", kicker: "Head to Head", labels: ["Hilux", "Rivals"], values: [92, 84], suffix: "%" }],
  ["Graf06_VersusTug", { title: "Global market preference", kicker: "Market Share", labels: ["Hilux", "Others"], values: [62, 38], suffix: "%" }],
  ["Graf07_TimelineRise", { title: "Production Milestones", kicker: "Growth", labels: ["2017", "2018", "2019", "2020", "2021", "2022"], values: [8, 10, 12, 14, 16, 18], suffix: "M" }],
  ["Graf08_LinePulse", { title: "Cumulative sales trajectory", kicker: "Trend", labels: [], values: [4, 7, 9, 12, 15, 18], suffix: "M" }],
  ["Graf09_RankList", { title: "Most reliable pickups", kicker: "Ranking", labels: ["Toyota Hilux", "Ford Ranger", "Isuzu D-Max", "Nissan Navara"], values: [92, 81, 74, 66], suffix: "%" }],
  ["Graf10_BigStatCard", { title: "Countries with active fleets", kicker: "Global Reach", values: [120, 140, 155, 170, 180], suffix: "" }],
  ["Graf11_PieSlices", { title: "Global production by plant", kicker: "Distribution", labels: ["Thailand", "South Africa", "Argentina", "Pakistan"], values: [45, 25, 18, 12] }],
  ["Graf12_MultiBars", { title: "Sales by region", kicker: "Markets", labels: ["Asia", "Oceania", "Africa", "Europe", "LatAm"], values: [64, 82, 47, 91, 73], suffix: "K" }],
  ["Graf13_DualLine", { title: "Reliability over 10 years", kicker: "Trend", labels: ["Hilux", "Avg. Competitor"], values: [6, 9, 12, 15, 18, 6, 7, 8, 9, 10] }],
  ["Graf14_OvlCounterPunch", { title: "Units Sold", kicker: "2020 Peak", values: [820], suffix: "K", bg: "__VID__", dim: 0.55 }],
  ["Graf15_OvlStatCorner", { title: "operational uptime across UN fleets", kicker: "Reliability", values: [92], suffix: "%", bg: "__VID__", dim: 0.45 }],
  ["Graf16_OvlProgressBar", { title: "Parts availability worldwide", kicker: "Coverage", values: [88], suffix: "%", bg: "__VID__", dim: 0.45 }],
];

const mont2 = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const vidBg = mont2.beats.find((b) => b.src && b.src.endsWith(".mp4") && b.tier === 1)?.src || "";
for (const c of CASOS) { if (c[1].bg === "__VID__") c[1].bg = vidBg; }
const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acgr") });
for (const [v, props] of CASOS) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, accent: "#f59e0b", ...props };
  const comp = await selectComposition({ serveUrl, id: "GraficoPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_GRAFICOS_DONE");
