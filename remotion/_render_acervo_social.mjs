// ALMOXARIFADO SOCIAL — 5 MP4s (IG, Reddit, X, Jornal, Portal) c/ grifo animado. Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acso");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_social";
mkdirSync(OUT, { recursive: true });

const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const foto = mont.beats.find((b) => b.src && /\.(jpg|png)$/i.test(b.src) && !b.src.includes("GEN"))?.src || "";

const CASOS = [
  ["Soc01_InstagramDM", {
    autor: "mike.overlander",
    texto: "Bro how many kms on your truck now? | 650,000 and counting | No engine rebuild?? | Nothing. It just refuses to die",
    grifo: "refuses to die" }],
  ["Soc02_RedditPost", {
    autor: "u/DieselFieldTech", handle: "r/MotorTrucks", curtidas: 4700,
    titulo: "10 years as a fleet mechanic in East Africa. One truck outlived them all.",
    texto: "We ran every brand through the same routes. Same loads, same drivers, same fuel. After 5 years only one platform kept a 92% uptime without dealer support.",
    grifo: "92% uptime without dealer support" }],
  ["Soc03_TweetPost", {
    autor: "Overland Diaries", handle: "@overland_diaries", curtidas: 18400, imagem: foto,
    texto: "Day 214 crossing 3 continents. Locals keep telling us the same thing: when nothing else survives the roads here, this truck does.",
    grifo: "when nothing else survives" }],
  ["Soc04_Newspaper", {
    kicker: "The Motor Chronicle", imagem: foto,
    titulo: "THE TRUCK THAT WOULD NOT DIE",
    texto: "Following a series of televised endurance trials, engineers confirmed the vehicle restarted after submersion, fire and a four-story drop — without structural repair. Industry veterans called the result unprecedented in modern automotive testing.",
    grifo: "without structural repair" }],
  ["Soc05_NewsSite", {
    kicker: "autoreport.news", autor: "Field Desk", imagem: foto,
    titulo: "UN fleet data reveals the most reliable pickup ever tested",
    texto: "Internal fleet logs reviewed by our team show a 92 percent operational uptime across humanitarian missions, a figure no competing platform matched over the same period.",
    grifo: "92 percent operational uptime" }],
];

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acso") });
for (const [v, props] of CASOS) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, accent: "#f59e0b", ...props };
  const comp = await selectComposition({ serveUrl, id: "SocialPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_SOCIAL_DONE");
