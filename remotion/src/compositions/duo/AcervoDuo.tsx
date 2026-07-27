import React from "react";
import { F_DISPLAY, F_SANS, F_MONO } from "../../fontes";
import { AbsoluteFill, OffthreadVideo, staticFile, interpolate, useCurrentFrame, useVideoConfig, spring, Easing } from "remotion";

/* ============================================================
   ALMOXARIFADO DUO DE VÍDEO (R-106, pedido Piter 22/07):
   dinamismo com 2 VÍDEOS na mesma cena. Contrato: { videos: [a, b], accent }.
   Injetado pelo MONTADOR (usa vídeos já baixados/aprovados do job,
   respeitando R-56). Sem 2 vídeos válidos => return null (R-30/32).
   ============================================================ */

type P = { videos?: string[]; captions?: string[]; accent?: string };
const SANS = F_SANS;

const Vid: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => (
  <OffthreadVideo src={staticFile(src)} muted loop
    style={{ width: "100%", height: "100%", objectFit: "cover", ...style }} />
);

/* 01 SPLIT — tela dividida, os dois entram dos lados com divisor luminoso */
export const Duo01_SplitVideos: React.FC<P> = ({ videos = [], captions = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!videos[0] || !videos[1]) return null;
  const s = spring({ frame: f, fps, config: { damping: 16, stiffness: 95 }, durationInFrames: 26 });
  const gl = 0.7 + 0.3 * Math.sin(f / 7);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "50%", overflow: "hidden",
        transform: `translateX(${(1 - s) * -100}%)` }}>
        <Vid src={videos[0]} style={{ transform: "scale(1.02)" }} />
        {captions[0] ? <div style={{ position: "absolute", bottom: 40, left: 40, fontFamily: SANS, fontWeight: 800,
          fontSize: 32, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>{captions[0]}</div> : null}
      </div>
      <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: "50%", overflow: "hidden",
        transform: `translateX(${(1 - s) * 100}%)` }}>
        <Vid src={videos[1]} style={{ transform: "scale(1.02)" }} />
        {captions[1] ? <div style={{ position: "absolute", bottom: 40, right: 40, fontFamily: SANS, fontWeight: 800,
          fontSize: 32, color: "#fff", textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>{captions[1]}</div> : null}
      </div>
      <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 6, transform: "translateX(-50%)",
        background: accent, boxShadow: `0 0 ${26 * gl}px ${accent}`, opacity: s }} />
    </AbsoluteFill>
  );
};

/* 02 SEQUENTIAL PUSH — A abre full; B entra empurrando A pra esquerda no meio do beat */
export const Duo02_SequentialPush: React.FC<P> = ({ videos = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  if (!videos[0] || !videos[1]) return null;
  const troca = Math.max(24, Math.round(durationInFrames * 0.42));
  const push = interpolate(f, [troca, troca + 22], [0, 100],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <AbsoluteFill style={{ transform: `translateX(${-push}%)` }}>
        <Vid src={videos[0]} />
      </AbsoluteFill>
      <AbsoluteFill style={{ transform: `translateX(${100 - push}%)` }}>
        <Vid src={videos[1]} />
      </AbsoluteFill>
      <div style={{ position: "absolute", top: 0, bottom: 0, width: 5, left: `${100 - push}%`,
        background: accent, boxShadow: `0 0 22px ${accent}`, opacity: push > 0 && push < 100 ? 1 : 0 }} />
    </AbsoluteFill>
  );
};

/* 03 PIP REVEAL — A full; B surge em janela flutuante no canto e cresce levemente */
export const Duo03_PipReveal: React.FC<P> = ({ videos = [], accent = "#f59e0b" }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!videos[0] || !videos[1]) return null;
  const s = spring({ frame: f - 20, fps, config: { damping: 14, stiffness: 100 }, durationInFrames: 24 });
  const zoom = interpolate(f, [44, 150], [1, 1.06], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Vid src={videos[0]} style={{ filter: "brightness(0.82)" }} />
      <div style={{ position: "absolute", right: 70, bottom: 70, width: 640, height: 360, borderRadius: 14,
        overflow: "hidden", border: `3px solid ${accent}`, boxShadow: `0 22px 60px rgba(0,0,0,0.65), 0 0 26px ${accent}55`,
        opacity: s, transform: `translateY(${(1 - s) * 60}px) scale(${zoom})`, transformOrigin: "bottom right" }}>
        <Vid src={videos[1]} />
      </div>
    </AbsoluteFill>
  );
};

export const DUO_COMPS: Record<string, React.FC<P>> = { Duo01_SplitVideos, Duo02_SequentialPush, Duo03_PipReveal };
