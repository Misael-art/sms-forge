# skill: sms-gameplay-experience-review

Use quando uma ROM, vertical slice ou build jogável precisar de avaliação
independente de game feel. Trabalhe read-only e separado do produtor.

## Entrada mínima

ROM + SHA, evidência de emulador da cena correta, roteiro/trace de input,
contrato de mecânica, público esperado.

## Julgue o que o jogador experimenta

- latência percebida, aceleração, hitstop, recovery (em frames)
- clareza de objetivo, ameaça, consequência e feedback
- decisão significativa e espaço para domínio
- onboarding, frustração e recuperação após erro
- relação entre câmera/scroll, colisão, animação, PSG e leitura da ação

Métrica sem sensação observável não prova game feel.
Sensação sem ROM/trace fica `needs_evidence`.
FPS estável não prova controle bom.
Para revisar gráficos/áudio/IA/HUD juntos e decidir crescimento, aplicar
`workflows/product-quality-checkpoint.md`. Alvo NTSC60/PAL50 é regional;
registre atraso entrada→reação→impacto/resultado separadamente de taxa média.
Um contador de ISR não prova que a lógica/render terminou a cada deadline.
Parecer de agente não é playtest com público nem valida aceitação de mercado.

## Saída

Bloco de domínio de `independent_quality_review`. Cada finding cita
frame/cena/input, impacto no jogador, menor correção e evidência de reteste.
Differencie `defect`, `risk`, `opportunity`, `taste`.

## Nunca faça

- declarar diversão por contrato ou screenshot
- autoaprovar o próprio trabalho
- bloquear por gosto
- reescrever mecânica sem autorização de escopo
- aceitar captura de boot como prova de luta/jogo
