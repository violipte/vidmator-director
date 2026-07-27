import { AbsoluteFill, Img, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// LOGO / FLAG GRID — grade de até 6 CARDS (logo/flag), cada um com o text; aparecem
// escalonados (spring pop). Container do acervo VidMator (ref.: VidRush "marcas/parceiros/países").
// Niche-agnostic via props. `image` (staticFile rel) mostra a marca/bandeira REAL; sem ela, cai
// no disco+inicial (fallback).
const DISPLAY = "'Archivo Black','Impact','Arial Black',sans-serif";
const SANS = "'Inter','Segoe UI',sans-serif";

type Item = { text: string; image?: string };

// paleta de matizes derivada do accent p/ diferenciar cards (giro de hue)
const HUES = [0, 40, 200, 150, 320, 90];

export const LogoFlagGrid: React.FC<{
  items?: Item[];
  accent?: string;
}> = ({
  items = [
    { text: "BRAND A" },
    { text: "BRAND B" },
    { text: "BRAND C" },
    { text: "BRAND D" },
    { text: "BRAND E" },
    { text: "BRAND F" },
  ],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shown = items.slice(0, 6);
  const cols = shown.length <= 4 ? Math.min(shown.length, 2) : 3;

  const titleIn = spring({ frame, fps, config: { damping: 18 }, durationInFrames: 20 });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(120% 100% at 50% 40%, #14161c 0%, #0a0b0f 74%)",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        fontFamily: SANS,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 64px)",
        }}
      />

      {/* barrinha decorativa accent */}
      <div
        style={{
          width: 120,
          height: 6,
          borderRadius: 3,
          marginBottom: 44,
          background: accent,
          boxShadow: `0 0 22px ${accent}`,
          opacity: titleIn,
          transform: `scaleX(${titleIn})`,
        }}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: 36,
          width: cols === 3 ? 1500 : 1000,
        }}
      >
        {shown.map((it, i) => {
          const pop = spring({ frame: frame - (14 + i * 8), fps, config: { damping: 13, stiffness: 130 }, durationInFrames: 18 });
          const hue = HUES[i % HUES.length];
          const initial = (it.text || "?").trim().charAt(0).toUpperCase();
          return (
            <div
              key={i}
              style={{
                height: 240,
                borderRadius: 16,
                background: "#14161c",
                border: "1px solid rgba(255,255,255,0.08)",
                boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 20,
                opacity: pop,
                transform: `scale(${0.7 + 0.3 * pop}) translateY(${(1 - pop) * 30}px)`,
              }}
            >
              {/* logo/bandeira REAL, se houver; senão disco+inicial (fallback) */}
              {it.image ? (
                <div
                  style={{
                    width: 158,
                    height: 100,
                    borderRadius: 12,
                    overflow: "hidden",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: 10,
                    background: "rgba(255,255,255,0.06)",
                    boxShadow: `0 8px 24px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.06)`,
                  }}
                >
                  <Img src={staticFile(it.image)} style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                </div>
              ) : (
                <div
                  style={{
                    width: 96,
                    height: 96,
                    borderRadius: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: DISPLAY,
                    fontSize: 52,
                    color: "#0a0b0f",
                    background: `hsl(${(parseInt(accentToHue(accent)) + hue) % 360} 85% 58%)`,
                    boxShadow: `0 8px 24px rgba(0,0,0,0.5)`,
                  }}
                >
                  {initial}
                </div>
              )}
              <div
                style={{
                  fontFamily: DISPLAY,
                  fontSize: 34,
                  letterSpacing: 2,
                  color: "#ffffff",
                  textAlign: "center",
                  padding: "0 12px",
                }}
              >
                {it.text}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// converte accent hex → hue aproximado (fallback âmbar ~38) p/ variar os discos coerente
function accentToHue(hex: string): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return "38";
  const n = parseInt(m[1], 16);
  const r = ((n >> 16) & 255) / 255;
  const g = ((n >> 8) & 255) / 255;
  const b = (n & 255) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const d = max - min;
  if (d === 0) return "38";
  let h = 0;
  if (max === r) h = ((g - b) / d) % 6;
  else if (max === g) h = (b - r) / d + 2;
  else h = (r - g) / d + 4;
  h = Math.round(h * 60);
  if (h < 0) h += 360;
  return String(h);
}
