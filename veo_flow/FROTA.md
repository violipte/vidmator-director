# FROTA de perfis do Flow — desenho de escala

> Desenho combinado com o Piter em 02/08, quando a frota tinha 2 perfis e o plano
> era chegar a ~11 (5 do plano família + 6 de um segundo Ultra).
> O objetivo aqui é que crescer seja **acrescentar uma linha**, não repensar o fluxo.

## A regra que define todo o resto

**O personagem vive no PROJETO. O projeto vive numa CONTA. Logo: um canal pertence
a uma conta e não migra sem perder o elenco.**

Não é preferência de organização — é consequência do Flow. Foi por isso que o
projeto virou "1 por canal" (projeto por vídeo matava o `@Russel`), e é por isso
que a unidade de roteamento é o **canal**, nunca o perfil.

Quando alguém pedir "gera esse vídeo", o fluxo não pergunta *qual perfil está
livre* — pergunta *de quem é esse canal*, e usa o perfil daquele dono. Perfil livre
de outro canal é território alheio, não recurso disponível (foi exatamente esse
erro que fez a automação do editor tomar o perfil do Claude do Flow em 02/08).

## Hierarquia

```
PLANO (Ultra / Família)
 └── CONTA Google  ──1:1──  PERFIL Chrome (veo_flow/chrome_profile_<nome>)
      └── PROJETO Flow  ──1:1──  CANAL          (personagens vivem aqui)
           └── COLEÇÃO  ──1:1──  VÍDEO          (elenco de vídeo vive aqui)
```

Cardinalidades que importam:
- 1 conta pode ter **vários canais** (vários projetos) — mas 1 canal só existe em 1 conta.
- 1 perfil só roda **um navegador por vez**; paralelismo real é entre PERFIS.
- Créditos são **por conta**: dois canais na mesma conta disputam o mesmo saldo.
  Distribuir canais entre contas é distribuir crédito, não só carga.

## Papéis (quem mexe em quê)

| dono | perfil | canais | responsável |
|---|---|---|---|
| `flow` | `chrome_profile` | AMZ (@Russel) | Claude do Flow — coleções, ciclo v2, personagens |
| `editor` | `chrome_profile_conta2` | (a definir) | Claude do Editor — gaps/ilustração do VidMator |

`veo_flow/perfis.py` guarda o dono e **nunca** entrega um perfil de outro dono,
mesmo que esteja livre. `veo_flow/frota.py` guarda conta ↔ perfil ↔ canais.

## Regimes de elenco (por canal)

Definem o que o gerador faz ANTES de gerar — ver `veo_flow/elenco.py`:

| regime | personagem vive | quando usar |
|---|---|---|
| `canal` | no projeto | canal com **host fixo** (o AMZ e o Russel) |
| `video` | na coleção | cada vídeo com gente própria (vítima, testemunha) |
| `nenhum` | — | b-roll/ilustração, sem gente (gaps do VidMator) |

Não declarado ⇒ **inferido** pelo `escopo` do personagem. Canal novo funciona sem
ninguém lembrar de configurar.

## Como crescer (o passo a passo real)

1. **Criar a conta** no plano (família ou novo Ultra).
2. `python veo_flow/perfis.py --novo <nome>` — cria `chrome_profile_<nome>`.
3. **Login manual, uma vez** — é o único passo humano, e é intencional:
   automatizar login do Google significa entregar credencial a um script, e o
   Flow tem reCAPTCHA Enterprise ativo.
   *(Atalho: com o Chrome FECHADO, `perfis.py --clonar "Profile N" <nome>` traz a
   sessão de um perfil já logado. Com o Chrome aberto o arquivo de cookies está em
   lock exclusivo e o clone nasce deslogado — medido em 02/08.)*
4. `python veo_flow/frota.py --registrar <nome> --conta <email> --plano ultra|familia`
5. Atribuir canais: `python veo_flow/frota.py --canal <SIGLA> --perfil <nome>`
6. Pronto. O roteamento passa a achar esse canal sozinho.

## Paralelismo

`banco-videos/teste/veo_paralelo.py` divide um lote entre os perfis **de um mesmo
dono** e dispara um driver por perfil. Round-robin, não blocos: se um perfil cai, o
prejuízo fica espalhado pelo lote em vez de matar um trecho inteiro do vídeo.

Vazão ≈ N× o número de perfis — a geração é dominada por espera de servidor, não
por CPU. O limite prático não é a máquina, é **crédito por conta** e o pacing
humano que o reCAPTCHA exige.

## O que NUNCA fazer

- **Rodar dois drivers no mesmo perfil.** O segundo cai em "Abrindo em uma sessão
  de navegador existente" e gera ZERO sem erro claro (custou uma fila inteira em
  02/08). O `perfis.py` existe para tornar isso visível.
- **Mover um canal de conta** sem recriar personagem e projeto. O `@Russel` não
  atravessa contas.
- **Mencionar personagem de outro vídeo** num canal de regime `video`. A menção
  falha silenciosamente e o take sai com rosto aleatório.
- **Tomar perfil livre de outro dono.** Livre ≠ disponível.

## UI nova do Flow (06/08) — perfil logado ≠ perfil utilizável

O Google está trocando a UI do Flow. A nova substitui a barra de prompt por um
painel de sessão ("O que você quer fazer?", sidebar Personagens/Cenas/Ferramentas)
e **não tem o seletor de modelo** que os drivers procuram. O sintoma cru é um
`TimeoutError` do Playwright esperando um botão que não existe mais.

O detalhe que confunde o diagnóstico:

| como se chega no projeto | UI servida |
|---|---|
| clique no card (navegação SPA) | antiga |
| `page.goto(.../project/<id>)`  | **nova** |

É o **mesmo projeto**. Por isso um teste que abre por clique dá VERDE num perfil
onde o driver — que navega por `goto` — morre. `smoke_perfis.py --ui` mede por
`goto` justamente para não mentir.

Consequência para a frota: **logado não basta**. Antes de atribuir um canal a um
perfil, rode `smoke_perfis.py --ui` e confirme "UI antiga". E `veo_driver --reusar`
abre projeto existente em vez de criar — além de não deixar projeto vazio na conta,
era o contorno que eu esperava para o rollout (não resolveu: o projeto existente
também vem novo por `goto`, mas a flag continua valendo pelo resto).

⚠️ O `flow_driver.py` (Claude do Flow) navega por `goto` em vários pontos e ainda
não trata esse caso — quando a UI nova chegar no `chrome_profile`, o ciclo de
coleções para. Vale olhar antes de virar incidente.
