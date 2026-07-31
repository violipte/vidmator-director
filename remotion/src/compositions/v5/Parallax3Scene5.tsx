import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   PARALLAX 2.5D (v5) — cena de 1-3 camadas com profundidade.
   fundo  = imagem cheia opaca (céu/ambiente distante)
   meio   = paisagem recortada (PNG alpha) — opcional
   frente = sujeito recortado (PNG alpha), ancorado pela base
   Movimentos: pushIn/pullOut/driftLeft/driftRight/float/sway,
   bgPanLeft/bgPanRight (bounded), bgScrollLeft/bgScrollRight
   (esteira infinita, 2 cópias lado a lado), scrollPushIn/Out.
   Profundidade = cada camada se move/escala em taxa diferente.
   ============================================================ */

export type ParallaxProps = {
  fundo?: string;
  meio?: string;
  frente?: string;
  mov?: string;      // default: pushIn
  tam?: number;      // fração da altura que a frente ocupa (default 0.52)
  pos?: number;      // centro horizontal da frente 0-1 (default 0.5)
  posv?: number;     // base da frente 0-1 (default 0.94)
  velbg?: number;    // multiplicador do movimento de fundo (default 1)
  velinout?: number; // multiplicador do push in/out (default 1)
};

const EASE = Easing.bezier(0.42, 0, 0.58, 1);

export const Parallax3Scene5: React.FC<ParallaxProps> = ({
  fundo, meio, frente, mov = "pushIn", tam = 0.52, pos = 0.5, posv = 0.94,
  velbg = 1, velinout = 1,
}) => {
  const f = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const t = Math.min(1, f / Math.max(1, durationInFrames - 1)); // 0→1 na cena
  const tE = interpolate(t, [0, 1], [0, 1], { easing: EASE });

  // ---- movimento por camada (profundidade: fundo < meio < frente) ----
  const esteira = mov.startsWith("bgScroll") || mov.startsWith("scrollPush");
  const push = (mov === "pushIn" || mov === "scrollPushIn") ? 1
    : (mov === "pullOut" || mov === "scrollPushOut") ? -1 : 0;

  // escala de push por profundidade (frente aproxima mais = sensação 2.5D)
  const zoomAmt = 0.10 * velinout;
  const zF = 1.0 + (push >= 0 ? tE : 1 - tE) * zoomAmt * (push !== 0 ? 0.55 : 0);
  const zM = 1.03 + (push >= 0 ? tE : 1 - tE) * zoomAmt * (push !== 0 ? 0.9 : 0);
  const zS = 1.0 + (push >= 0 ? tE : 1 - tE) * zoomAmt * (push !== 0 ? 1.5 : 0);

  // drift lateral por profundidade
  const driftDir = mov === "driftLeft" ? -1 : mov === "driftRight" ? 1 : 0;
  const dxF = driftDir * tE * width * 0.02 * velbg;
  const dxM = driftDir * tE * width * 0.045 * velbg;
  const dxS = driftDir * tE * width * 0.08 * velbg;

  // pan do fundo (bounded — vai e volta suave dentro do overscan)
  const panDir = mov === "bgPanLeft" ? -1 : mov === "bgPanRight" ? 1 : 0;
  const pan = panDir * Math.sin(t * Math.PI) * width * 0.06 * velbg;

  // esteira infinita: translate contínuo com módulo (2 cópias do fundo)
  const scrollDir = (mov === "bgScrollLeft") ? -1 : (mov === "bgScrollRight" || mov.startsWith("scrollPush")) ? 1 : 0;
  const scrollPx = scrollDir !== 0 ? ((f * 1.6 * velbg) % width) * scrollDir : 0;

  // órbita / rotação do fundo
  const orbita = mov === "bgOrbit" ? 1 : 0;
  const orbX = orbita * Math.sin(t * 2 * Math.PI) * width * 0.03 * velbg;
  const orbY = orbita * Math.cos(t * 2 * Math.PI) * height * 0.02 * velbg;
  const rotBg = mov === "bgRotate" ? Math.sin(t * Math.PI) * 2.2 * velbg : 0;

  // float/sway (respiração)
  const bob = mov === "float" ? Math.sin((f / 30) * 1.8) * height * 0.012 : 0;
  const sway = mov === "sway" ? Math.sin((f / 30) * 1.4) * width * 0.015 : 0;

  // overscan por camada (esteira/pan pedem mais)
  const overF = esteira || panDir !== 0 || orbita ? 1.28 : 1.14;
  const overM = 1.16;

  const frenteH = height * tam;

  return (
    <AbsoluteFill style={{ background: "#06070b" }}>
      {/* FUNDO — opaco, cheio */}
      {fundo && (esteira ? (
        // 2 cópias lado a lado deslizando com módulo = céu infinito
        <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
          {[0, 1].map((k) => (
            <Img key={k} src={staticFile(fundo)} style={{
              position: "absolute", top: "50%", left: 0,
              width: width * overF, height: height * overF,
              objectFit: "cover",
              transform: `translate(${-scrollPx + (k - 0.5) * width * overF * (scrollDir >= 0 ? 1 : -1) - (overF - 1) * width * 0.5}px, -50%) scale(${zF})`,
            }} />
          ))}
        </div>
      ) : (
        <Img src={staticFile(fundo)} style={{
          position: "absolute", top: `${-(overF - 1) * 50}%`, left: `${-(overF - 1) * 50}%`,
          width: `${overF * 100}%`, height: `${overF * 100}%`, objectFit: "cover",
          transform: `translate(${dxF + pan + orbX + sway}px, ${orbY + bob}px) scale(${zF}) rotate(${rotBg}deg)`,
        }} />
      ))}
      {/* MEIO — recortado (alpha), paisagem */}
      {meio && (
        <Img src={staticFile(meio)} style={{
          position: "absolute", top: `${-(overM - 1) * 50}%`, left: `${-(overM - 1) * 50}%`,
          width: `${overM * 100}%`, height: `${overM * 100}%`, objectFit: "cover", objectPosition: "center bottom",
          transform: `translate(${dxM + pan * 0.45 + sway * 0.5}px, ${bob * 0.5}px) scale(${zM})`,
        }} />
      )}
      {/* FRENTE — sujeito recortado, ancorado pela BASE (posv) */}
      {frente && (
        <div style={{
          position: "absolute",
          left: pos * width, top: posv * height,
          transform: `translate(-50%, -100%) translate(${dxS + sway * 0.2}px, ${bob * 0.35}px) scale(${zS})`,
          transformOrigin: "50% 100%",
          height: frenteH, maxWidth: width * 0.9,
          filter: "drop-shadow(0 24px 30px rgba(0,0,0,0.5))",
        }}>
          <Img src={staticFile(frente)} style={{ height: "100%", width: "auto" }} />
        </div>
      )}
      {/* vinheta leve pra assentar as camadas */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 88% 88% at 50% 46%, transparent 60%, rgba(0,0,0,0.38) 100%)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
