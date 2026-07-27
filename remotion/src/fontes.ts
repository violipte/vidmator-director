/* ============================================================
   FONTES POR TEMA (R-107, Piter 22/07) — identidade tipográfica por NICHO.
   Fonte da verdade: style_card.fonte_tema ∈ {impact|serif|typewriter|clean}
   (o fontes.py escolhe por LLM; montagem.json carrega; Montagem injeta).
   Tudo Google Fonts (OFL/Apache — uso comercial OK), load determinístico
   via @remotion/google-fonts: o render NUNCA depende de fonte do Windows.
   ============================================================ */
import { loadFont as fAnton } from "@remotion/google-fonts/Anton";
import { loadFont as fInter } from "@remotion/google-fonts/Inter";
import { loadFont as fJet } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as fPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as fLora } from "@remotion/google-fonts/Lora";
import { loadFont as fPlexMono } from "@remotion/google-fonts/IBMPlexMono";
import { loadFont as fElite } from "@remotion/google-fonts/SpecialElite";
import { loadFont as fCourier } from "@remotion/google-fonts/CourierPrime";
import { loadFont as fGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as fSpaceMono } from "@remotion/google-fonts/SpaceMono";

const ANTON = fAnton().fontFamily;
const INTER = fInter().fontFamily;
const JET = fJet().fontFamily;
const PLAYFAIR = fPlayfair().fontFamily;
const LORA = fLora().fontFamily;
const PLEXMONO = fPlexMono().fontFamily;
const ELITE = fElite().fontFamily;
const COURIER = fCourier().fontFamily;
const GROTESK = fGrotesk().fontFamily;
const SPACEMONO = fSpaceMono().fontFamily;

export type FonteTema = "impact" | "serif" | "typewriter" | "clean";

export type Tipografia = { display: string; body: string; mono: string };

export const TEMAS: Record<FonteTema, Tipografia> = {
  /* true crime, automotivo, choque, breaking */
  impact: {
    display: `'${ANTON}', 'Arial Black', sans-serif`,
    body: `'${INTER}', 'Segoe UI', sans-serif`,
    mono: `'${JET}', 'Consolas', monospace`,
  },
  /* história, biografia, filosofia, épico */
  serif: {
    display: `'${PLAYFAIR}', 'Georgia', serif`,
    body: `'${LORA}', 'Georgia', serif`,
    mono: `'${PLEXMONO}', 'Courier New', monospace`,
  },
  /* mistério, dossiê, investigação, noir */
  typewriter: {
    display: `'${ELITE}', 'Courier New', monospace`,
    body: `'${COURIER}', 'Courier New', monospace`,
    mono: `'${COURIER}', 'Courier New', monospace`,
  },
  /* saúde, ciência, tech, explicativo */
  clean: {
    display: `'${GROTESK}', 'Segoe UI', sans-serif`,
    body: `'${INTER}', 'Segoe UI', sans-serif`,
    mono: `'${SPACEMONO}', 'Consolas', monospace`,
  },
};

export const getTema = (nome?: string): Tipografia =>
  TEMAS[(nome as FonteTema) || "impact"] || TEMAS.impact;

/* Tema ATIVO do job (tema_atual.ts é gerado pelo montador por vídeo).
   O acervo importa estas três — R-107: nenhum componente com stack hardcoded. */
import { TEMA_JOB } from "./tema_atual";
const ATIVO = getTema(TEMA_JOB);
export const F_DISPLAY = ATIVO.display;
export const F_SANS = ATIVO.body;
export const F_MONO = ATIVO.mono;
