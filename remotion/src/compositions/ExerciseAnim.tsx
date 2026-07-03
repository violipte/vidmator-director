import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from "remotion";

// Demonstração de exercício ANIMADA (faceless) — estilo "tech/neon": fundo preto + grade,
// boneco verde-neon com brilho, setas de movimento, props (chão/parede/cadeira) e passo-a-passo EN.

type J = "head" | "shoulder" | "elbow" | "hand" | "hip" | "knee" | "foot";
type Pose = Record<J, [number, number]>;
type Dir = "up" | "down" | "fwd" | "back";
type Arrow = { x: number; y: number; dir: Dir; len?: number };
type Prop = "wall" | "chair";

const LIMBS: [J, J, number][] = [
  ["shoulder", "hip", 22], ["shoulder", "elbow", 15], ["elbow", "hand", 13],
  ["hip", "knee", 19], ["knee", "foot", 15],
];

const GREEN = "#39ff14";   // verde neon
const ARROW = "#ffd23f";   // âmbar (setas de movimento — contrasta com o verde)

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerpPose = (a: Pose, b: Pose, t: number): Pose => {
  const o = {} as Pose;
  (Object.keys(a) as J[]).forEach((k) => { o[k] = [lerp(a[k][0], b[k][0], t), lerp(a[k][1], b[k][1], t)]; });
  return o;
};

const Figure: React.FC<{ pose: Pose }> = ({ pose }) => (
  <g strokeLinecap="round" stroke={GREEN} fill="none" filter="url(#neon)">
    {LIMBS.map(([p, q, w], i) => (
      <line key={i} x1={pose[p][0]} y1={pose[p][1]} x2={pose[q][0]} y2={pose[q][1]} strokeWidth={w} />
    ))}
    <line x1={pose.head[0]} y1={pose.head[1] + 16} x2={pose.shoulder[0]} y2={pose.shoulder[1]} strokeWidth={13} />
    <circle cx={pose.head[0]} cy={pose.head[1]} r={21} fill={GREEN} stroke="none" />
  </g>
);

// seta de movimento: shaft + cabeça, pulsa/desliza na direção do movimento
const NeonArrow: React.FC<{ a: Arrow }> = ({ a }) => {
  const f = useCurrentFrame();
  const p = (f % 26) / 26;                 // loop
  const op = Math.sin(p * Math.PI);        // fade in/out
  const off = p * 16;                       // desliza na direção
  const d = a.len ?? 46;
  const [dx, dy] = a.dir === "up" ? [0, -1] : a.dir === "down" ? [0, 1] : a.dir === "fwd" ? [1, 0] : [-1, 0];
  const tipX = a.x + dx * off, tipY = a.y + dy * off;
  const tailX = tipX - dx * d, tailY = tipY - dy * d;
  // cabeça da seta (triângulo) perpendicular à direção
  const px = -dy, py = dx, h = 13, bw = 9;
  const head = `${tipX},${tipY} ${tipX - dx * h + px * bw},${tipY - dy * h + py * bw} ${tipX - dx * h - px * bw},${tipY - dy * h - py * bw}`;
  return (
    <g filter="url(#neonA)" opacity={op}>
      <line x1={tailX} y1={tailY} x2={tipX - dx * 10} y2={tipY - dy * 10} stroke={ARROW} strokeWidth={7} strokeLinecap="round" />
      <polygon points={head} fill={ARROW} />
    </g>
  );
};

export type Exercise = {
  nome: string; reps: string; steps: string[]; speed: number; A: Pose; B: Pose; arrows: Arrow[]; props?: Prop[];
};

// poses (viewBox 0 0 480 360, chão ~y320, perfil virado à direita). steps em EN.
export const EXERCISES: Record<string, Exercise> = {
  squat: {
    nome: "Deep Squat", reps: "x 15", speed: 0.055,
    steps: ["Feet shoulder-width apart", "Hips back and down", "Thighs parallel, chest up"],
    arrows: [{ x: 300, y: 210, dir: "down" }],
    A: { head: [240, 60], shoulder: [238, 108], elbow: [252, 150], hand: [262, 192], hip: [240, 196], knee: [238, 258], foot: [240, 318] },
    B: { head: [238, 110], shoulder: [236, 152], elbow: [266, 176], hand: [292, 178], hip: [232, 214], knee: [288, 252], foot: [244, 318] },
  },
  pushup: {
    nome: "Push-Up", reps: "x 12", speed: 0.06,
    steps: ["Body in a straight line", "Elbows about 45 degrees", "Lower chest, then press up"],
    arrows: [{ x: 220, y: 235, dir: "down" }],
    A: { head: [150, 206], shoulder: [170, 214], elbow: [152, 258], hand: [150, 302], hip: [284, 238], knee: [352, 276], foot: [408, 300] },
    B: { head: [150, 250], shoulder: [170, 258], elbow: [136, 290], hand: [150, 302], hip: [284, 268], knee: [352, 290], foot: [408, 304] },
  },
  plank: {
    nome: "Plank Hold", reps: "30s", speed: 0.03,
    steps: ["Forearms under shoulders", "Hips level, core tight", "Hold steady, breathe"],
    arrows: [{ x: 286, y: 200, dir: "down", len: 30 }],
    A: { head: [150, 208], shoulder: [172, 216], elbow: [168, 262], hand: [164, 302], hip: [286, 240], knee: [354, 278], foot: [410, 300] },
    B: { head: [150, 212], shoulder: [172, 220], elbow: [168, 264], hand: [164, 302], hip: [286, 246], knee: [354, 280], foot: [410, 302] },
  },
  legraise: {
    nome: "Leg Raise", reps: "x 12", speed: 0.05,
    steps: ["Lie flat, lower back pressed down", "Lift legs toward 90 degrees", "Lower slowly, don't touch floor"],
    arrows: [{ x: 360, y: 250, dir: "up" }],
    A: { head: [148, 292], shoulder: [184, 300], elbow: [214, 320], hand: [246, 322], hip: [292, 300], knee: [352, 300], foot: [412, 300] },
    B: { head: [148, 292], shoulder: [184, 300], elbow: [214, 320], hand: [246, 322], hip: [292, 300], knee: [332, 234], foot: [336, 166] },
  },
  lunge: {
    nome: "Forward Lunge", reps: "x 10 / side", speed: 0.05,
    steps: ["Step forward, torso tall", "Front knee over ankle", "Drop back knee, drive up"],
    arrows: [{ x: 300, y: 250, dir: "down" }],
    A: { head: [240, 60], shoulder: [238, 108], elbow: [246, 152], hand: [252, 196], hip: [240, 196], knee: [238, 258], foot: [240, 318] },
    B: { head: [232, 92], shoulder: [232, 138], elbow: [244, 180], hand: [252, 214], hip: [228, 222], knee: [300, 274], foot: [306, 318] },
  },
  horse: {
    nome: "Horse Stance", reps: "45s", speed: 0.025,
    steps: ["Feet wide, toes forward", "Sink hips, thighs parallel", "Spine straight, hold (Mabu)"],
    arrows: [{ x: 240, y: 210, dir: "down", len: 34 }],
    A: { head: [240, 92], shoulder: [238, 136], elbow: [206, 158], hand: [196, 196], hip: [240, 196], knee: [196, 248], foot: [176, 318] },
    B: { head: [240, 100], shoulder: [238, 144], elbow: [206, 166], hand: [196, 204], hip: [240, 206], knee: [192, 256], foot: [172, 318] },
  },
  glute_bridge: {
    nome: "Glute Bridge", reps: "x 15", speed: 0.05,
    steps: ["Lie on back, knees bent, feet flat", "Drive hips up, squeeze glutes", "Straight line knees to shoulders"],
    arrows: [{ x: 278, y: 280, dir: "up" }],
    A: { head: [148, 294], shoulder: [186, 298], elbow: [152, 314], hand: [120, 318], hip: [278, 298], knee: [336, 262], foot: [332, 318] },
    B: { head: [148, 294], shoulder: [186, 298], elbow: [152, 314], hand: [120, 318], hip: [278, 256], knee: [336, 250], foot: [332, 318] },
  },
  mountain_climber: {
    nome: "Mountain Climber", reps: "x 20", speed: 0.07,
    steps: ["Start in a high plank", "Drive one knee toward chest", "Switch fast, keep hips low"],
    arrows: [{ x: 320, y: 256, dir: "fwd" }],
    A: { head: [150, 205], shoulder: [172, 212], elbow: [166, 258], hand: [160, 300], hip: [286, 236], knee: [354, 272], foot: [410, 298] },
    B: { head: [150, 205], shoulder: [172, 212], elbow: [166, 258], hand: [160, 300], hip: [286, 238], knee: [306, 250], foot: [276, 278] },
  },
  superman: {
    nome: "Superman", reps: "x 12", speed: 0.045,
    steps: ["Lie face down, arms extended", "Lift arms, chest and legs", "Squeeze, hold, lower slow"],
    arrows: [{ x: 372, y: 270, dir: "up" }, { x: 104, y: 282, dir: "up" }],
    A: { head: [338, 298], shoulder: [300, 300], elbow: [330, 312], hand: [366, 300], hip: [196, 300], knee: [146, 300], foot: [104, 300] },
    B: { head: [342, 268], shoulder: [300, 278], elbow: [332, 258], hand: [372, 248], hip: [196, 300], knee: [146, 284], foot: [104, 262] },
  },
  crunch: {
    nome: "Crunch", reps: "x 20", speed: 0.06,
    steps: ["Lie back, knees bent", "Curl shoulders toward knees", "Lower slow, don't pull the neck"],
    arrows: [{ x: 182, y: 272, dir: "up" }],
    A: { head: [150, 288], shoulder: [186, 294], elbow: [206, 308], hand: [168, 292], hip: [280, 300], knee: [336, 262], foot: [332, 318] },
    B: { head: [196, 250], shoulder: [214, 266], elbow: [230, 288], hand: [200, 256], hip: [280, 300], knee: [336, 262], foot: [332, 318] },
  },
  calf_raise: {
    nome: "Calf Raise", reps: "x 20", speed: 0.06,
    steps: ["Stand tall, feet together", "Rise onto the balls of your feet", "Pause at the top, lower slow"],
    arrows: [{ x: 300, y: 180, dir: "up" }],
    A: { head: [240, 72], shoulder: [240, 118], elbow: [246, 160], hand: [252, 202], hip: [240, 200], knee: [240, 260], foot: [240, 318] },
    B: { head: [240, 58], shoulder: [240, 104], elbow: [246, 146], hand: [252, 188], hip: [240, 186], knee: [240, 248], foot: [244, 318] },
  },
  wall_sit: {
    nome: "Wall Sit", reps: "45s", speed: 0.02, props: ["wall"],
    steps: ["Back flat against the wall", "Slide down to 90 degree knees", "Hold, weight in your heels"],
    arrows: [{ x: 66, y: 262, dir: "down", len: 24 }],
    A: { head: [66, 150], shoulder: [66, 196], elbow: [96, 222], hand: [124, 250], hip: [66, 240], knee: [190, 240], foot: [190, 318] },
    B: { head: [66, 154], shoulder: [66, 200], elbow: [96, 224], hand: [124, 252], hip: [66, 244], knee: [190, 244], foot: [190, 318] },
  },
  cobra: {
    nome: "Cobra Stretch", reps: "30s", speed: 0.03,
    steps: ["Lie face down, hands by ribs", "Press chest up, shoulders back", "Keep your hips grounded"],
    arrows: [{ x: 330, y: 268, dir: "up" }],
    A: { head: [336, 298], shoulder: [298, 300], elbow: [324, 314], hand: [348, 318], hip: [198, 300], knee: [148, 302], foot: [106, 300] },
    B: { head: [342, 236], shoulder: [300, 256], elbow: [326, 300], hand: [348, 318], hip: [202, 300], knee: [148, 302], foot: [106, 300] },
  },
  bird_dog: {
    nome: "Bird Dog", reps: "x 12 / side", speed: 0.04,
    steps: ["On hands and knees, back flat", "Extend opposite arm and leg", "Reach long, keep hips level"],
    arrows: [{ x: 356, y: 202, dir: "fwd" }, { x: 118, y: 224, dir: "back" }],
    A: { head: [300, 212], shoulder: [278, 220], elbow: [268, 252], hand: [274, 300], hip: [212, 224], knee: [232, 268], foot: [248, 300] },
    B: { head: [300, 212], shoulder: [278, 220], elbow: [326, 206], hand: [362, 196], hip: [212, 224], knee: [162, 228], foot: [112, 222] },
  },
};

export const ExerciseAnim: React.FC<{ ex: Exercise; idx?: number }> = ({ ex, idx }) => {
  const f = useCurrentFrame();
  const t = (Math.sin(f * ex.speed * Math.PI - Math.PI / 2) + 1) / 2;
  const pose = lerpPose(ex.A, ex.B, t);
  const appear = interpolate(f, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{
      backgroundColor: "#05070a", fontFamily: "'Poppins','Segoe UI',system-ui,sans-serif",
      backgroundImage: "linear-gradient(rgba(57,255,20,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(57,255,20,0.06) 1px, transparent 1px)",
      backgroundSize: "56px 56px",
    }}>
      {/* vinheta */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 38% 52%, transparent 40%, rgba(0,0,0,0.78) 100%)", pointerEvents: "none" }} />

      {/* nº faint */}
      {idx != null && (
        <div style={{ position: "absolute", top: 54, left: 90, fontSize: 210, fontWeight: 800, color: GREEN, opacity: 0.10, lineHeight: 1 }}>{idx}</div>
      )}

      {/* nome + reps (topo) */}
      <div style={{ position: "absolute", top: 84, width: "100%", textAlign: "center", opacity: appear }}>
        <div style={{ fontSize: 80, fontWeight: 800, color: "#eafff2", letterSpacing: -1, textShadow: `0 0 24px rgba(57,255,20,0.45)` }}>{ex.nome}</div>
        <div style={{ display: "inline-block", marginTop: 14, padding: "8px 30px", borderRadius: 40, border: `2px solid ${GREEN}`, color: GREEN, fontSize: 40, fontWeight: 700, boxShadow: `0 0 22px rgba(57,255,20,0.5)`, textShadow: `0 0 14px ${GREEN}` }}>{ex.reps}</div>
      </div>

      {/* figura à esquerda-centro */}
      <svg viewBox="0 0 480 360" style={{ position: "absolute", left: "3%", top: "50%", transform: `translateY(-50%) scale(${0.92 + 0.08 * appear})`, width: 900, height: 675 }}>
        <defs>
          <filter id="neon" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="neonA" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* PROPS: chão sempre; parede/cadeira se o exercício pedir */}
        <line x1="40" y1="322" x2="440" y2="322" stroke={GREEN} strokeWidth="2.5" opacity="0.5" filter="url(#neonA)" />
        {ex.props?.includes("wall") && <line x1="56" y1="60" x2="56" y2="322" stroke={GREEN} strokeWidth="3" opacity="0.5" filter="url(#neonA)" />}
        {ex.props?.includes("chair") && (
          <g stroke={GREEN} strokeWidth="3" fill="none" opacity="0.55" filter="url(#neonA)">
            <rect x="300" y="250" width="92" height="10" /><line x1="300" y1="260" x2="300" y2="322" /><line x1="392" y1="260" x2="392" y2="322" /><line x1="392" y1="250" x2="392" y2="150" />
          </g>
        )}

        <Figure pose={pose} />
        {ex.arrows.map((a, i) => <NeonArrow key={i} a={a} />)}
      </svg>

      {/* passo-a-passo (EN) à direita */}
      <div style={{ position: "absolute", right: 96, top: "50%", transform: "translateY(-50%)", width: 600, opacity: appear }}>
        {ex.steps.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", marginBottom: 40 }}>
            <div style={{ width: 64, height: 64, flexShrink: 0, borderRadius: "50%", border: `2.5px solid ${GREEN}`, color: GREEN, fontSize: 34, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 18px rgba(57,255,20,0.5)`, textShadow: `0 0 10px ${GREEN}` }}>{i + 1}</div>
            <div style={{ marginLeft: 24, color: "#eafff2", fontSize: 38, fontWeight: 600, lineHeight: 1.25 }}>{s}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const ExerciseGallery: React.FC = () => {
  const { fps } = useVideoConfig();
  const dur = Math.round(3.8 * fps);
  const keys = Object.keys(EXERCISES);
  return (
    <AbsoluteFill>
      {keys.map((k, i) => (
        <Sequence key={k} from={i * dur} durationInFrames={dur}>
          <ExerciseAnim ex={EXERCISES[k]} idx={i + 1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
