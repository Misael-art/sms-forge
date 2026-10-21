# skill: sms-video-evidence

**Quando usar:** o claim é sobre algo que ACONTECE — transição de estado,
animação, game feel, "o golpe conecta", "a vitória aparece". Screenshot não
serve: um PNG não tem eixo do tempo (§36, L054). Para tela estática e fidelidade
de arte, continue no `capture_evidence.py`.

## O canal

O Emulicious grava do **framebuffer**, não da tela:

- **256×192 exatos** — a canvas do VDP, sem moldura, sem barra de menu, sem
  desktop. Não existe recorte a fazer, e por construção não há como vazar
  conteúdo pessoal do usuário (§30/L017).
- Encode por **FFMPEG externo** (`FFMPEGPath` no `Emulicious.ini`).
- Atalho: propriedades do `.ini` com prefixo **`Keys`** —
  `KeysStartVideoRecording=F7`, `KeysStopVideoRecording=F8`. **Sem essas linhas
  não há atalho nenhum**, a ação só existe no menu. `capture_video.py` as
  instala (com o emulador parado) e `--probe-shortcut` as confere.

```sh
python3 tools/sms_wrapper/capture_video.py \
    --project SMS_projects/<proj> --rom out/rom/<nome>.sms \
    --seconds 8 --out video_<eixo> --press 'Right=500,Left=500'
```

Saída: `out/evidence/<out>.mp4`, N frames-chave PNG e um bundle
`emulator_evidence_v2` (superset do v1: `screenshot` continua presente). O
`.mp4` e os frames entram no `seal_fresh_evidence_bundle.py` como qualquer
outro artefato — o selo não precisou mudar.

## O que o gate mede

| Gate | Reprova |
|---|---|
| `ffprobe` dimensão | ≠ 256×192 → é captura de tela, não framebuffer |
| frames / duração | < 60 frames ou < 1s → gravação não chegou a rodar |
| luma dos frames | último frame vazio, ou maioria vazia |
| `motion_fraction` | < 1% entre o primeiro e o último → tela congelada |

O **primeiro frame costuma ser preto** e isso é correto: a gravação começa antes
do VDP desenhar. A amostra fica no bundle em vez de ser escondida; o critério é
o último frame ter conteúdo e a maioria ter.

## Falhas MUDAS deste canal (§45)

Todas já aconteceram aqui, e as três produzem sintoma que parece sucesso:

1. **Instância zumbi.** Um Emulicious de outra sessão rouba o foco **e reescreve
   o `Emulicious.ini` ao morrer**, apagando o atalho recém-instalado. O gate
   aborta se achar outro Emulicious vivo — `pkill -f Emulicious.jar` antes.
2. **F10 não para a gravação.** No Swing/AWT, F10 é o atalho nativo da barra de
   menus. A gravação seguia aberta e era finalizada só quando o processo morria,
   entregando um `.mp4` válido que *parecia* prova de que o atalho funcionou.
3. **Mover o arquivo cedo o corrompe.** O FFMPEG reabre o `.mp4` depois de parar
   de escrever, para gravar o atom `moov`. Critério de término = o ffprobe
   conseguir ler. O nome de saída é `<rom>.mp4`, não `temp.mp4` (esses são
   intermediários).

## Limite honesto

O vídeo prova que **a ROM desta build renderizou e que a imagem mudou**. Não
prova mecânica correta nem que a mudança é a pretendida — isso continua exigindo
olho humano (`sms-gameplay-experience-review`) ou um medidor específico
(deslocamento do objeto controlado, §29).

**A trilha de áudio agora vem junto, e prova menos do que parece.** O `.mp4`
saía mudo porque o `temp.wav` do emulador declara no chunk `data` **o dobro dos
bytes que existem**; o FFMPEG batia em EOF na metade e descartava a trilha. O
`attach_audio()` percorre os chunks RIFF, usa os bytes que existem e lê
taxa/canais/bits do próprio `fmt ` — nada é constante, então mono/estéreo e
44,1k/22k funcionam igual. Não era o host mudo: com o host **desmutado a 15%** o
mp4 continuava sem trilha.

O que a trilha sustenta: **havia som saindo da ROM**. Não que é a música certa
nas notas certas (§28) — isso continua sendo `capture_audio.py` (§31), cujo sink
nulo é imune ao volume do host. Payload mudo (`peak=0`) **não é anexado**:
trilha silenciosa deixaria alguém alegar som (L048). E o remux nunca encurta o
vídeo — a primeira versão usava `-shortest`, cortou 455 → 452 frames, e o guard
de contagem de frames recusou o resultado.

**Não confunda com a L055.** O que ela recusa é MP4/GIF de *mood* gerado por
ferramenta de arte apresentado como prova de ROM. Vídeo do framebuffer do
emulador rodando a ROM selada é o oposto: tem cadeia de custódia.
