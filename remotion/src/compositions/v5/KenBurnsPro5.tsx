import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";

/* ============================================================
   KEN BURNS SEMÂNTICO (v5 F4) — 11 tipos nomeados; o diretor
   escolhe pela NATUREZA do beat (produto, detalhe, época, ação).
   Inset -8% esconde bordas durante o movimento; progresso cobre
   a duração INTEIRA do clipe (nunca congela antes do fim).
   ============================================================ */

export type KenBurnsTipo =
  | "productShot" | "detailShot" | "archiveShot" | "actionShot"
  | "smoothZoomPan" | "zoomOutReveal" | "verticalPan" | "steadyDrift"
  | "punchZoom" | "focusPan" | "rotateZoom";

const EASE = Easing.bezier(0.42, 0, 0.58, 1);

export const KenBurnsPro5: React.FC<{ src: string; kb?: string }> = ({ src, kb = "steadyDrift" }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(Math.min(1, f / Math.max(1, durationInFrames - 1)), [0, 1], [0, 1], { easing: EASE });

  let scale = 1.1, tx = 0, ty = 0, rot = 0;
  switch (kb) {
    case "productShot":   scale = 1.04 + t * 0.12; break;
    case "detailShot":    scale = 1.10 + t * 0.20; tx = -t * 4; ty = -t * 3; break;
    case "archiveShot":   scale = 1.18 - t * 0.12; tx = t * 2; break;
    case "actionShot":    scale = 1.12 + t * 0.12; tx = -t * 5; ty = t * 2.5; break;
    case "smoothZoomPan": scale = 1.08 + t * 0.10; tx = t * 4.5; break;
    case "zoomOutReveal": scale = 1.30 - t * 0.24; break;
    case "verticalPan":   scale = 1.16; ty = interpolate(t, [0, 1], [3.2, -3.2]); break;
    case "steadyDrift":   scale = 1.08 + t * 0.04; tx = t * 1.6; ty = -t * 1.2; break;
    case "punchZoom":     scale = 1.0 + interpolate(t, [0, 0.4, 1], [0, 0.2, 0.23], { easing: Easing.out(Easing.cubic) }); break;
    case "focusPan":      scale = 1.20; tx = interpolate(t, [0, 1], [4, -4]); break;
    case "rotateZoom":    scale = 1.05 + t * 0.17; rot = interpolate(t, [0, 1], [-3.5, 3.5]); break;
  }
  return (
    <Img src={staticFile(src)} style={{
      position: "absolute", inset: "-8%", width: "116%", height: "116%",
      objectFit: "cover",
      transform: `translate(${tx}%, ${ty}%) scale(${scale}) rotate(${rot}deg)`,
    }} />
  );
};

/* mapa semântico: o montador escolhe por natureza do beat */
export const KB_POR_NATUREZA: Record<string, KenBurnsTipo[]> = {
  produto: ["productShot", "detailShot", "punchZoom"],
  epoca: ["archiveShot", "zoomOutReveal", "steadyDrift"],
  acao: ["actionShot", "smoothZoomPan", "punchZoom"],
  paisagem: ["smoothZoomPan", "focusPan", "verticalPan"],
  generico: ["steadyDrift", "smoothZoomPan", "rotateZoom", "zoomOutReveal"],
};
