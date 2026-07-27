// ALMOXARIFADO MAPAS — 12 MP4s (geo validada + auto-fit + satélite/ruas ESRI). Resumível.
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve } from "path";
import { mkdirSync, existsSync, writeFileSync, readFileSync } from "fs";

const TMP = resolve("_tmp_acmp");
mkdirSync(TMP, { recursive: true });
process.env.TMP = process.env.TEMP = process.env.TMPDIR = TMP;
const OUT = "F:/Canal Dark/Aplicativo de Edição/banco-videos/_acervo_mapas";
mkdirSync(OUT, { recursive: true });
const SAT = resolve("public/sat");
mkdirSync(SAT, { recursive: true });

/* ---- fetch ESRI (mesmo endpoint do satelite_fetch.py; 960x540, gl=angle safe) ---- */
const R = 6378137;
const merc = (lon, lat) => [(lon * Math.PI / 180) * R, Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * R];
async function baixar(servico, cx, cy, half, nome) {
  const dest = resolve(SAT, nome);
  if (existsSync(dest)) return true;
  const hh = half * 540 / 960;
  const url = `https://services.arcgisonline.com/ArcGIS/rest/services/${servico}/MapServer/export?bbox=${cx - half},${cy - hh},${cx + half},${cy + hh}&bboxSR=3857&imageSR=3857&size=960,540&format=jpg&f=image`;
  const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" } });
  const buf = Buffer.from(await r.arrayBuffer());
  if (buf[0] !== 0xff || buf[1] !== 0xd8 || buf.length < 8000) { console.log("tile inválido:", nome); return false; }
  writeFileSync(dest, buf);
  console.log("sat OK", nome);
  return true;
}

const HALFS = [1500000, 330000, 73000, 16000, 3600, 800];
const dubai = merc(55.27, 25.2);
const durban = merc(31.02, -29.86);
const alice = merc(133.88, -23.7);
// rota Abu Dhabi -> Dubai (mapa de ruas): bbox centrado no meio, meia-largura cobrindo os 2
const AD = merc(54.38, 24.45), DXB = merc(55.27, 25.2);
const rcx = (AD[0] + DXB[0]) / 2, rcy = (AD[1] + DXB[1]) / 2;
const halfRota = Math.max(Math.abs(DXB[0] - AD[0]) / 2 * 1.5, (Math.abs(DXB[1] - AD[1]) / 2 * 1.5) * 960 / 540);
const hhRota = halfRota * 540 / 960;
const BBOX_ROTA = [rcx - halfRota, rcy - hhRota, rcx + halfRota, rcy + hhRota];

let satOk = true;
for (let i = 0; i < HALFS.length; i++) satOk = (await baixar("World_Imagery", dubai[0], dubai[1], HALFS[i], `acmp_dubai_${i}.jpg`)) && satOk;
satOk = (await baixar("World_Imagery", durban[0], durban[1], 3600, "acmp_durban.jpg")) && satOk;
satOk = (await baixar("World_Imagery", alice[0], alice[1], 73000, "acmp_alice.jpg")) && satOk;
satOk = (await baixar("World_Street_Map", rcx, rcy, halfRota, "acmp_rota_uae.jpg")) && satOk;
if (!satOk) { console.log("ERRO: tiles satélite faltando — abortando pra não renderizar vazio"); process.exit(1); }

// foto real do job pro Map13 (mesmo esquema do acervo social/imagem)
const mont = JSON.parse(readFileSync(resolve("public/jobs/hilux_mont/montagem.json"), "utf-8"));
const foto = mont.beats.find((b) => b.src && /\.(jpg|png)$/i.test(b.src) && !b.src.includes("GEN"))?.src || "";
if (!foto) { console.log("ERRO: nenhuma foto no job pro Map13"); process.exit(1); }

const CASOS = [
  ["Map01_CountryFocus", { paises: ["Thailand"], titulo: "Thailand", kicker: "Production Hub" }],
  ["Map02_MultiHighlight", { paises: ["Thailand", "South Africa", "Argentina"], valores: ["Main plant", "Africa hub", "LATAM plant"], kicker: "Global Production" }],
  ["Map03_RouteArc", { pontos: [{ nome: "Tehran", lat: 35.69, lon: 51.39 }, { nome: "Dubai", lat: 25.2, lon: 55.27 }], kicker: "Export Route" }],
  ["Map04_PinCallout", { pontos: [{ nome: "Durban", lat: -29.86, lon: 31.02 }], titulo: "Assembly Plant", kicker: "South Africa" }],
  ["Map05_RegionZoom", { paises: ["Australia"], titulo: "Australia", kicker: "The Outback Market" }],
  ["Map06_PathTrail", { pontos: [
      { nome: "Nairobi", lat: -1.29, lon: 36.82 },
      { nome: "Addis Ababa", lat: 9.03, lon: 38.74 },
      { nome: "Khartoum", lat: 15.5, lon: 32.56 },
      { nome: "Cairo", lat: 30.04, lon: 31.24 },
    ], kicker: "The Expedition" }],
  ["Map07_RadarSweep", { pontos: [{ nome: "Test Zone", lat: -23.7, lon: 133.88 }], kicker: "Endurance Trials" }],
  ["Map08_StatMap", { paises: ["Australia"], valores: ["45%"], titulo: "of all pickups sold", kicker: "Market Share" }],
  ["Map09_EarthZoom", { pontos: [{ nome: "Dubai", lat: 25.2, lon: 55.27 }],
    sat: [0, 1, 2, 3, 4, 5].map((i) => `sat/acmp_dubai_${i}.jpg`), halfs: HALFS }],
  ["Map10_SatPinApp", { pontos: [{ nome: "Durban", lat: -29.86, lon: 31.02 }], titulo: "Assembly Plant",
    sat: ["sat/acmp_durban.jpg"], accent: "#ea4335" }],
  ["Map11_StreetRoute", { pontos: [{ nome: "Abu Dhabi", lat: 24.45, lon: 54.38 }, { nome: "Dubai", lat: 25.2, lon: 55.27 }],
    sat: ["sat/acmp_rota_uae.jpg"], bbox: BBOX_ROTA, kicker: "Delivery Run", accent: "#2f6fed" }],
  ["Map12_SatTarget", { pontos: [{ nome: "Test Range", lat: -23.7, lon: 133.88 }],
    sat: ["sat/acmp_alice.jpg"] }],
  ["Map13_CineLocation", { images: [foto], paises: ["Thailand"], pontos: [{ nome: "Bangkok", lat: 13.76, lon: 100.5 }],
    titulo: "Production Hub", kicker: "On Location" }],
];

const serveUrl = await bundle({ entryPoint: resolve("src/index.ts"), outDir: resolve("_bundle_acmp") });
for (const [v, props] of CASOS) {
  const dest = `${OUT}/${v}.mp4`;
  if (existsSync(dest)) { console.log("skip", v); continue; }
  const inputProps = { variante: v, accent: "#f59e0b", ...props };
  const comp = await selectComposition({ serveUrl, id: "MapaPreview", inputProps });
  await renderMedia({ composition: comp, serveUrl, codec: "h264", outputLocation: dest, inputProps,
    pixelFormat: "yuv420p", crf: 20, concurrency: 10, imageFormat: "jpeg", jpegQuality: 90,
    chromiumOptions: { gl: "angle" }, muted: true });
  console.log("OK", v);
}
console.log("ACERVO_MAPAS_DONE");
