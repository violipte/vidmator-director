import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO SOCIAL/MÍDIA — 5 variações (2026-07-20, ref. VidRush).
   Conversa IG · Post Reddit · Post X · Artigo de jornal · Matéria de site.
   Todos com HIGHLIGHT animado (grifo) no trecho-chave.
   CONTRATO: { autor, handle, titulo, texto, grifo, imagem?, curtidas?, kicker?, accent }
   REGRA: identidades SEMPRE fictícias (nunca perfil/veículo real).
   ============================================================ */

type P = { autor?: string; handle?: string; titulo?: string; texto?: string; grifo?: string;
  imagem?: string; curtidas?: number; kicker?: string; accent?: string };
const DISPLAY = F_DISPLAY;
const SERIF = "'Georgia','Times New Roman',serif";
const MONO = F_MONO;
const SANS = F_SANS;

/* grifo animado: marca-texto varrendo o trecho `grifo` dentro de `texto` */
const Grifado: React.FC<{ texto: string; grifo?: string; sweep: number; cor: string; estilo?: React.CSSProperties }> = ({ texto, grifo, sweep, cor, estilo }) => {
  if (!grifo || !texto.toLowerCase().includes(grifo.toLowerCase())) return <span style={estilo}>{texto}</span>;
  const i = texto.toLowerCase().indexOf(grifo.toLowerCase());
  return (
    <span style={estilo}>
      {texto.slice(0, i)}
      <span style={{ backgroundImage: `linear-gradient(${cor}66, ${cor}66)`, backgroundRepeat: "no-repeat", backgroundSize: `${sweep}% 62%`, backgroundPosition: "0 68%", borderRadius: 3 }}>
        {texto.slice(i, i + grifo.length)}
      </span>
      {texto.slice(i + grifo.length)}
    </span>
  );
};

const Avatar: React.FC<{ nome: string; cor: string; tam?: number }> = ({ nome, cor, tam = 74 }) => (
  <div style={{ width: tam, height: tam, borderRadius: "50%", background: `linear-gradient(135deg, ${cor}, #2a2f3a)`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 800, fontSize: tam * 0.42, color: "#fff", flexShrink: 0 }}>
    {(nome || "?").slice(0, 1).toUpperCase()}
  </div>
);

/* 01 INSTAGRAM DM — conversa: balões entrando em sequência + digitando */
export const Soc01_InstagramDM: React.FC<P> = ({ autor = "mike.overlander", texto = "", grifo = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const msgs = (texto || "").split("|").map((m) => m.trim()).filter(Boolean);
  const sweep = interpolate(f, [msgs.length * 16 + 10, msgs.length * 16 + 40], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#0b0d12", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 900, background: "#000", borderRadius: 34, border: "1px solid rgba(255,255,255,0.14)", overflow: "hidden", boxShadow: "0 40px 100px rgba(0,0,0,0.7)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "22px 30px", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ fontSize: 30, color: "#fff" }}>‹</div>
          <div style={{ width: 58, height: 58, borderRadius: "50%", background: "linear-gradient(45deg, #f09433, #e6683c, #dc2743, #bc1888)", padding: 3 }}>
            <Avatar nome={autor} cor="#333" tam={52} />
          </div>
          <div>
            <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 27, color: "#fff" }}>{autor}</div>
            <div style={{ fontFamily: SANS, fontSize: 20, color: "#8a8f98" }}>Active now</div>
          </div>
        </div>
        <div style={{ padding: "30px 26px 36px", display: "flex", flexDirection: "column", gap: 16 }}>
          {msgs.map((m, i) => {
            const s = spring({ frame: f - i * 16, fps, config: { damping: 14, stiffness: 130 }, durationInFrames: 18 });
            const minha = i % 2 === 1;
            const ultima = i === msgs.length - 1;
            return (
              <div key={i} style={{ alignSelf: minha ? "flex-end" : "flex-start", maxWidth: "76%", opacity: s, transform: `translateY(${(1 - s) * 26}px) scale(${0.9 + 0.1 * s})`,
                background: minha ? "linear-gradient(135deg, #7b3ff2, #b02ecc)" : "#262a33", color: "#fff",
                padding: "16px 24px", borderRadius: minha ? "24px 24px 6px 24px" : "24px 24px 24px 6px",
                fontFamily: SANS, fontSize: 27, lineHeight: 1.4 }}>
                {m}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 02 REDDIT POST — card com upvotes contando + selftext com grifo */
export const Soc02_RedditPost: React.FC<P> = ({ autor = "u/DieselFieldTech", handle = "r/MotorTrucks", titulo = "", texto = "", grifo = "", curtidas = 4700, accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 24 });
  const votos = Math.round(interpolate(f, [10, 60], [0, curtidas], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  const sweep = interpolate(f, [46, 84], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [88, 126], [1, 1.11], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#0c0e12", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 1240, background: "#16181c", borderRadius: 18, border: "1px solid rgba(255,255,255,0.12)", padding: "30px 36px", opacity: s, transformOrigin: "38% 58%", transform: `translateY(${(1 - s) * 40}px) scale(${zoom})`, boxShadow: "0 40px 100px rgba(0,0,0,0.7)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 18 }}>
          <div style={{ width: 52, height: 52, borderRadius: "50%", background: "#ff4500", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SANS, fontWeight: 800, fontSize: 26, color: "#fff" }}>r/</div>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 26, color: "#e8eaee" }}>{handle}</span>
          <span style={{ fontFamily: SANS, fontSize: 22, color: "#7d828c" }}>· Posted by {autor} · 7h</span>
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 42, color: "#fff", lineHeight: 1.25, marginBottom: 18 }}>{titulo}</div>
        <div style={{ fontFamily: SANS, fontSize: 29, lineHeight: 1.5, color: "#c9cdd5", marginBottom: 26 }}>
          <Grifado texto={texto} grifo={grifo} sweep={sweep} cor={accent} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 34 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, background: "#0f1114", borderRadius: 22, padding: "10px 22px" }}>
            <span style={{ color: "#ff4500", fontSize: 30 }}>▲</span>
            <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28, color: "#ff4500" }}>{votos >= 1000 ? (votos / 1000).toFixed(1) + "k" : votos}</span>
            <span style={{ color: "#7d828c", fontSize: 30 }}>▼</span>
          </div>
          <span style={{ fontFamily: SANS, fontSize: 25, color: "#7d828c" }}>💬 892 comments</span>
          <span style={{ fontFamily: SANS, fontSize: 25, color: "#7d828c" }}>⤴ Share</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 03 X / TWEET — card dark com verificado, grifo e contadores subindo */
export const Soc03_TweetPost: React.FC<P> = ({ autor = "Overland Diaries", handle = "@overland_diaries", texto = "", grifo = "", imagem = "", curtidas = 18400, accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 100 }, durationInFrames: 24 });
  const likes = Math.round(interpolate(f, [12, 62], [0, curtidas], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  const sweep = interpolate(f, [40, 78], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [82, 120], [1, 1.10], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const k = (n: number) => (n >= 1000 ? (n / 1000).toFixed(1) + "K" : String(n));
  return (
    <AbsoluteFill style={{ background: "#080a0d", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 1160, background: "#000", borderRadius: 20, border: "1px solid #2f3336", padding: "34px 40px", opacity: s, transformOrigin: "42% 34%", transform: `scale(${(0.94 + 0.06 * s) * zoom})`, boxShadow: "0 40px 100px rgba(0,0,0,0.8)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 20 }}>
          <Avatar nome={autor} cor={accent} tam={72} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 29, color: "#e7e9ea" }}>{autor}</span>
              <span style={{ width: 26, height: 26, borderRadius: "50%", background: "#1d9bf0", color: "#fff", fontSize: 17, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800 }}>✓</span>
            </div>
            <span style={{ fontFamily: SANS, fontSize: 24, color: "#71767b" }}>{handle}</span>
          </div>
          <span style={{ fontFamily: DISPLAY, fontSize: 40, color: "#e7e9ea" }}>𝕏</span>
        </div>
        <div style={{ fontFamily: SANS, fontSize: 34, lineHeight: 1.42, color: "#e7e9ea", marginBottom: imagem ? 22 : 26 }}>
          <Grifado texto={texto} grifo={grifo} sweep={sweep} cor={accent} />
        </div>
        {imagem ? <Img src={staticFile(imagem)} style={{ width: "100%", height: 420, objectFit: "cover", borderRadius: 18, border: "1px solid #2f3336", marginBottom: 22 }} /> : null}
        <div style={{ display: "flex", gap: 60, fontFamily: SANS, fontSize: 25, color: "#71767b" }}>
          <span>💬 {k(Math.round(likes * 0.04))}</span>
          <span>🔁 {k(Math.round(likes * 0.18))}</span>
          <span style={{ color: "#f91880" }}>♥ {k(likes)}</span>
          <span>📊 2.1M</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 04 NEWSPAPER — broadsheet serifado com grifo animado no trecho */
export const Soc04_Newspaper: React.FC<P> = ({ kicker = "THE MOTOR CHRONICLE", titulo = "", texto = "", grifo = "", imagem = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 90 }, durationInFrames: 26 });
  const sweep = interpolate(f, [44, 84], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [88, 128], [1, 1.12], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "linear-gradient(160deg, #14120e 0%, #0b0a08 100%)", justifyContent: "center", alignItems: "center" }}>
      <div style={{ background: "#efe9da", width: 1240, padding: "48px 62px 46px", transformOrigin: "68% 74%", transform: `rotate(${-1.2 + 0.8 * s}deg) scale(${(0.9 + 0.1 * s) * zoom})`, opacity: s, boxShadow: "0 50px 120px rgba(0,0,0,0.8)" }}>
        <div style={{ textAlign: "center", borderBottom: "4px double #26221a", paddingBottom: 14, marginBottom: 8 }}>
          <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 52, color: "#1c1812", letterSpacing: 3 }}>{kicker.toUpperCase()}</div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 18, color: "#6b6350", borderBottom: "1.5px solid #26221a", padding: "6px 0", marginBottom: 22 }}>
          <span>VOL. LXXXVII — No. 24,118</span><span>MORNING EDITION</span><span>PRICE 25¢</span>
        </div>
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 58, color: "#171310", lineHeight: 1.1, textAlign: "center", marginBottom: 24 }}>{titulo}</div>
        <div style={{ display: "flex", gap: 34 }}>
          {imagem ? <Img src={staticFile(imagem)} style={{ width: 480, height: 330, objectFit: "cover", filter: "grayscale(1) contrast(1.1)", border: "1px solid #26221a" }} /> : null}
          <div style={{ flex: 1, fontFamily: SERIF, fontSize: 27, lineHeight: 1.52, color: "#26221a", textAlign: "justify" }}>
            <Grifado texto={texto} grifo={grifo} sweep={sweep} cor={accent} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 05 NEWS SITE — matéria de portal: chrome de browser + masthead + grifo */
export const Soc05_NewsSite: React.FC<P> = ({ kicker = "autoreport.news", autor = "Field Desk", titulo = "", texto = "", grifo = "", imagem = "", accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 95 }, durationInFrames: 26 });
  const sweep = interpolate(f, [48, 88], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [92, 130], [1, 1.12], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#0b0d11", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: 1300, borderRadius: 18, overflow: "hidden", border: "1px solid rgba(255,255,255,0.14)", opacity: s, transformOrigin: "50% 82%", transform: `translateY(${(1 - s) * 44}px) scale(${zoom})`, boxShadow: "0 46px 110px rgba(0,0,0,0.75)" }}>
        <div style={{ background: "#f7f6f2", padding: "34px 52px 44px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `4px solid ${accent}`, paddingBottom: 12, marginBottom: 24 }}>
            <span style={{ fontFamily: DISPLAY, fontSize: 38, color: "#16161a", letterSpacing: 1 }}>{kicker.split(".")[0].toUpperCase()}<span style={{ color: accent }}>.</span>{kicker.split(".")[1] ?? "news"}</span>
            <span style={{ fontFamily: SANS, fontWeight: 700, fontSize: 20, color: "#fff", background: "#c22", padding: "6px 16px", borderRadius: 6 }}>EXCLUSIVE</span>
          </div>
          <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: 50, color: "#141418", lineHeight: 1.15, marginBottom: 12 }}>{titulo}</div>
          <div style={{ fontFamily: SANS, fontSize: 21, color: "#6d7078", marginBottom: 22 }}>By {autor} · Updated 2 hours ago</div>
          {imagem ? <Img src={staticFile(imagem)} style={{ width: "100%", height: 380, objectFit: "cover", borderRadius: 10, marginBottom: 24 }} /> : null}
          <div style={{ fontFamily: SERIF, fontSize: 29, lineHeight: 1.55, color: "#232327" }}>
            <Grifado texto={texto} grifo={grifo} sweep={sweep} cor={accent} />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------------- MANIFESTO ---------------- */
export const SOCIAL_MANIFEST = [
  { id: 0, comp: "Soc01_InstagramDM", quando: "conversa/DM (texto = mensagens separadas por '|'; grifo na última)" },
  { id: 1, comp: "Soc02_RedditPost", quando: "relato de comunidade/anônimo (upvotes contam)" },
  { id: 2, comp: "Soc03_TweetPost", quando: "declaração pública/viral (com imagem opcional)" },
  { id: 3, comp: "Soc04_Newspaper", quando: "fato histórico/imprensa de época (P&B)" },
  { id: 4, comp: "Soc05_NewsSite", quando: "notícia atual/portal (browser + EXCLUSIVE)" },
];

export const SOCIAL_COMPS: Record<string, React.FC<P>> = {
  Soc01_InstagramDM, Soc02_RedditPost, Soc03_TweetPost, Soc04_Newspaper, Soc05_NewsSite,
};
