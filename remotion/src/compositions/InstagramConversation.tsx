import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// INSTAGRAM CONVERSATION — balões de chat surgindo 1 a 1 (spring pop) como conversa real.
// Recebido (esq, cinza) / enviado (dir, azul). Fundo dark. Container do acervo VidMator.
// Niche-agnostic via prop `messages`.
const SANS = "'Inter', 'Segoe UI', sans-serif";

type Msg = { from: "in" | "out"; text: string };

export const InstagramConversation: React.FC<{
  messages?: Msg[];
  accent?: string;
}> = ({
  messages = [
    { from: "in", text: "Hi! did you hear about this?" },
    { from: "out", text: "Nah, what's that?" },
    { from: "in", text: "It's an AI powered video tool." },
    { from: "out", text: "Really? How can I use it?" },
  ],
  accent = "#f59e0b",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const STAGGER = 26; // frames entre balões
  const START = 14;
  const outOp = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#0a0b0f", justifyContent: "center", alignItems: "center", fontFamily: SANS, opacity: outOp, overflow: "hidden" }}>
      {/* halo accent sutil */}
      <AbsoluteFill style={{ background: `radial-gradient(70% 60% at 50% 45%, ${accent}12 0%, transparent 60%)` }} />

      {/* moldura de "telefone" / painel de chat */}
      <div
        style={{
          width: 900,
          maxHeight: 940,
          background: "#14161c",
          borderRadius: 32,
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          padding: "34px 40px 44px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* header do chat */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 18,
            paddingBottom: 24,
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            marginBottom: 30,
          }}
        >
          <div style={{ width: 60, height: 60, borderRadius: "50%", background: `linear-gradient(135deg, ${accent}, #7c3aed)` }} />
          <div>
            <div style={{ color: "#ffffff", fontSize: 30, fontWeight: 700 }}>direct</div>
            <div style={{ color: "#5b6472", fontSize: 20 }}>Active now</div>
          </div>
        </div>

        {/* balões */}
        <div style={{ display: "flex", flexDirection: "column", gap: 22, justifyContent: "flex-end" }}>
          {messages.map((m, i) => {
            const t0 = START + i * STAGGER;
            const e = spring({ frame: frame - t0, fps, config: { damping: 13, stiffness: 130 }, durationInFrames: 16 });
            const op = interpolate(frame - t0, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const isOut = m.from === "out";
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: isOut ? "flex-end" : "flex-start",
                  opacity: op,
                  transform: `scale(${interpolate(e, [0, 1], [0.6, 1])}) translateY(${(1 - e) * 20}px)`,
                  transformOrigin: isOut ? "right bottom" : "left bottom",
                }}
              >
                <div
                  style={{
                    maxWidth: "72%",
                    padding: "20px 28px",
                    fontSize: 32,
                    lineHeight: 1.3,
                    color: isOut ? "#ffffff" : "#e6e9ee",
                    background: isOut ? "linear-gradient(135deg, #3897f0, #2563eb)" : "#262a33",
                    borderRadius: 28,
                    borderBottomRightRadius: isOut ? 8 : 28,
                    borderBottomLeftRadius: isOut ? 28 : 8,
                    boxShadow: "0 6px 18px rgba(0,0,0,0.4)",
                  }}
                >
                  {m.text}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
