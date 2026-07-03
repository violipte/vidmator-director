import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

// CTA de YouTube personalizado e animado: LIKE + SUBSCRIBE + BELL, com uma mãozinha
// que "clica" cada um em sequência. Niche-agnóstico, sem stock/green-screen.

const YT_RED = "#ff0033";
const TXT = "#ffffff";
const SUB = "#aeb6c2";
const PANEL = "rgba(10,14,22,0.92)";
const FONT = "'Segoe UI', system-ui, sans-serif";

const seg = (t: number, a: number, b: number) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const eo = Easing.out(Easing.cubic);

// ---- ícones (SVG paths) ----
const ThumbIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg width={46} height={46} viewBox="0 0 24 24" fill={color}>
    <path d="M2 21h2.5V9H2v12zM22 10c0-1.1-.9-2-2-2h-5.31l.95-4.57.03-.32a1.5 1.5 0 0 0-.44-1.06L14.17 1 7.6 7.59A2 2 0 0 0 7 9v9c0 1.1.9 2 2 2h8c.7 0 1.36-.42 1.65-1.06l3.02-7.05c.22-.5.33-1.05.33-1.59V10z" />
  </svg>
);
const BellIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg width={44} height={44} viewBox="0 0 24 24" fill={color}>
    <path d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-5v-1l-2-2v-3a5 5 0 0 0-4-4.9V6a1 1 0 1 0-2 0v.1A5 5 0 0 0 7 11v3l-2 2v1h14z" />
  </svg>
);
const HandCursor: React.FC = () => (
  <svg width={90} height={90} viewBox="0 0 64 64" style={{ filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.6))" }}>
    <path d="M28 6c-2 0-3.5 1.6-3.5 3.5V30l-3-4.5c-1-1.6-3.2-2-4.7-1-1.5 1-1.8 3-.8 4.6l7 12c1.6 2.8 4.6 4.9 8.5 4.9h6c5 0 9-4 9-9V20c0-2-1.5-3.5-3.5-3.5S40 18 40 20v-2c0-2-1.5-3.5-3.5-3.5S33 16 33 18v-2.5c0-2-1.5-3.5-3.5-3.5S26 13.5 26 15.5V9.5C26 7.6 27.5 6 28 6z" fill="#f3f6fb" stroke="#0b1020" strokeWidth={2} strokeLinejoin="round" />
  </svg>
);

const Ripple: React.FC<{ p: number }> = ({ p }) =>
  p <= 0 || p >= 1 ? null : (
    <span style={{
      position: "absolute", left: "50%", top: "50%",
      width: 120, height: 120, marginLeft: -60, marginTop: -60, borderRadius: "50%",
      border: `3px solid ${TXT}`, opacity: (1 - p) * 0.6, transform: `translate(-0%,0) scale(${0.3 + p * 1.1})`,
      pointerEvents: "none",
    }} />
  );

export const YtCta: React.FC<{ durFrames: number; headline?: string }> = ({ durFrames, headline = "ENJOYING THE VIDEO?" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const inn = spring({ frame, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 18 });
  const out = interpolate(frame, [durFrames - 14, durFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const op = Math.min(inn, out);

  // momentos de clique (s): like, subscribe, bell
  const T_LIKE = 0.7, T_SUB = 1.7, T_BELL = 2.8;

  // LIKE: aперта no clique
  const likeTap = Math.sin(Math.PI * seg(t, T_LIKE, T_LIKE + 0.35));
  const likeScale = 1 - 0.18 * likeTap;
  const liked = t > T_LIKE + 0.1;
  const plusOne = seg(t, T_LIKE, T_LIKE + 0.7); // "+1" sobe e some

  // SUBSCRIBE: pressiona + brilho + vira "SUBSCRIBED"
  const subTap = Math.sin(Math.PI * seg(t, T_SUB, T_SUB + 0.35));
  const subScale = 1 - 0.1 * subTap;
  const subscribed = t > T_SUB + 0.25;
  const subGlow = seg(t, T_SUB, T_SUB + 0.5) * (1 - seg(t, T_SUB + 0.5, T_SUB + 1.3));

  // BELL: toca (gira) + badge
  const ringP = seg(t, T_BELL, T_BELL + 0.8);
  const bellRot = Math.sin(ringP * Math.PI * 6) * 22 * (1 - ringP);
  const badge = spring({ frame: frame - Math.round((T_BELL + 0.15) * fps), fps, config: { damping: 10, stiffness: 180 }, durationInFrames: 14 });

  // mãozinha: vai pra LIKE -> SUBSCRIBE -> BELL (posições x relativas ao centro)
  const X_LIKE = -300, X_SUB = 20, X_BELL = 330, Y_REST = 150, Y_TAP = 40;
  let hx = X_LIKE, hy = Y_REST;
  const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
  if (t < T_LIKE) { hx = lerp(X_LIKE - 120, X_LIKE, seg(t, 0.2, T_LIKE)); hy = lerp(260, Y_REST, seg(t, 0.2, T_LIKE)); }
  else if (t < T_SUB) { hx = lerp(X_LIKE, X_SUB, seg(t, T_LIKE + 0.3, T_SUB)); }
  else if (t < T_BELL) { hx = lerp(X_SUB, X_BELL, seg(t, T_SUB + 0.3, T_BELL)); }
  else { hx = X_BELL; }
  const tapNow = likeTap + subTap + Math.max(0, Math.sin(Math.PI * seg(t, T_BELL, T_BELL + 0.3)));
  hy = (t < T_LIKE ? hy : Y_REST) - 26 * Math.min(1, tapNow);

  const Btn: React.FC<{ children: React.ReactNode; bg: string; scale?: number; glow?: number; w?: number }> = ({ children, bg, scale = 1, glow = 0, w }) => (
    <div style={{
      position: "relative", display: "flex", alignItems: "center", justifyContent: "center", gap: 12,
      height: 78, minWidth: w || 150, padding: "0 26px", borderRadius: 14, background: bg,
      transform: `scale(${scale})`, boxShadow: glow ? `0 0 ${22 * glow}px ${10 * glow}px rgba(255,0,51,${0.5 * glow})` : "0 6px 18px rgba(0,0,0,0.45)",
      color: TXT, fontFamily: FONT, fontWeight: 800, fontSize: 30, letterSpacing: 0.5,
    }}>{children}</div>
  );

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 120, opacity: op }}>
      <div style={{
        position: "relative", display: "flex", flexDirection: "column", alignItems: "center", gap: 18,
        padding: "26px 40px 30px", borderRadius: 22, background: PANEL, border: "1px solid rgba(255,255,255,0.08)",
        boxShadow: "0 18px 60px rgba(0,0,0,0.6)", transform: `translateY(${(1 - inn) * 60}px) scale(${0.94 + inn * 0.06})`,
      }}>
        <div style={{ color: SUB, fontFamily: FONT, fontWeight: 700, fontSize: 26, letterSpacing: 2, textTransform: "uppercase" }}>{headline}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
          {/* LIKE */}
          <div style={{ position: "relative" }}>
            <Btn bg={liked ? "#1b3a8f" : "rgba(255,255,255,0.10)"} scale={likeScale}>
              <ThumbIcon color={liked ? "#7cb0ff" : TXT} /> LIKE
              <Ripple p={seg(t, T_LIKE, T_LIKE + 0.5)} />
            </Btn>
            {plusOne > 0 && plusOne < 1 && (
              <span style={{ position: "absolute", left: 30, top: -10, color: "#7cb0ff", fontFamily: FONT, fontWeight: 900, fontSize: 30, opacity: 1 - plusOne, transform: `translateY(${-plusOne * 50}px)` }}>+1</span>
            )}
          </div>
          {/* SUBSCRIBE */}
          <div style={{ position: "relative" }}>
            <Btn bg={subscribed ? "#3a3f4b" : YT_RED} scale={subScale} glow={subGlow} w={subscribed ? 220 : 200}>
              {subscribed ? "SUBSCRIBED ✓" : "SUBSCRIBE"}
              <Ripple p={seg(t, T_SUB, T_SUB + 0.5)} />
            </Btn>
          </div>
          {/* BELL */}
          <div style={{ position: "relative" }}>
            <Btn bg="rgba(255,255,255,0.10)" w={92}>
              <span style={{ display: "inline-block", transform: `rotate(${bellRot}deg)`, transformOrigin: "50% 20%" }}>
                <BellIcon color={t > T_BELL ? "#ffd34d" : TXT} />
              </span>
              <Ripple p={seg(t, T_BELL, T_BELL + 0.5)} />
            </Btn>
            {badge > 0.02 && (
              <span style={{ position: "absolute", right: 6, top: 2, minWidth: 26, height: 26, borderRadius: 13, background: YT_RED, color: TXT, fontFamily: FONT, fontWeight: 900, fontSize: 17, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${badge})` }}>1</span>
            )}
          </div>
        </div>
        {/* mãozinha clicando */}
        <div style={{ position: "absolute", left: "50%", top: "62%", transform: `translate(${hx}px, ${hy}px)`, pointerEvents: "none" }}>
          <HandCursor />
        </div>
      </div>
    </AbsoluteFill>
  );
};
