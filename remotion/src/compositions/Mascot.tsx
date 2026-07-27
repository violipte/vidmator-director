import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

// MASCOTE do canal (personagem recortado, PNG alpha) — entra a cada 2-3 cenas com POP de mola,
// fica com um idle sutil (bob + sway) e sai rápido no fim da janela. Lado alterna por cena (pass mascote.py).

type Props = {
  imgRel: string;              // ex: "test/mascote/galo_pointing.png"
  lado?: "left" | "right";
  sceneFrames: number;         // duração da janela (frames)
  alturaFrac?: number;         // fração da altura do vídeo (default 0.46)
};

export const Mascot: React.FC<Props> = ({ imgRel, lado = "right", sceneFrames, alturaFrac = 0.46 }) => {
  const f = useCurrentFrame();
  const { fps, height } = useVideoConfig();

  // ENTRADA: mola com overshoot (pop de baixo, inclinado pra dentro)
  const pop = spring({ frame: f, fps, config: { damping: 11, stiffness: 160, mass: 0.7 } });
  // SAÍDA: encolhe nos últimos 12 frames
  const outStart = Math.max(1, sceneFrames - 12);
  const sai = interpolate(f, [outStart, sceneFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  // IDLE: bob vertical + sway sutil de rotação (vivo, não estático)
  const bob = Math.sin((f / fps) * 2.4) * 6;
  const sway = Math.sin((f / fps) * 1.7 + 1) * 1.2;

  const h = height * alturaFrac;
  const tiltIn = lado === "right" ? -3 : 3;
  const escala = pop * sai;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: -8 + bob * pop,
          [lado]: 34,
          height: h,
          transform: `scale(${escala}) rotate(${tiltIn * (1 - pop) + sway}deg)`,
          transformOrigin: lado === "right" ? "bottom right" : "bottom left",
          filter: "drop-shadow(0 18px 22px rgba(0,0,0,0.45))",
        }}
      >
        <Img src={staticFile(imgRel)} style={{ height: "100%", width: "auto" }} />
      </div>
    </AbsoluteFill>
  );
};
