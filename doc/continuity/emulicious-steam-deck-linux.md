# Restaurar o controle do Deck no Emulicious

Use o checkout de continuidade do SMSForge. Prepare as dependências fixadas pelo [bootstrap do host](20261024-start-here.md). O `Emulicious.jar` deve ficar em `tools/emuladores/emulicious/` junto do launcher. Use o Java do bootstrap ou um Java compatível no `PATH`. A integração KDE Desktop usa Python com `evdev`, SDL2 com suporte HID do Steam Deck, Bubblewrap, acesso do usuário ao Deck e `/dev/uinput`.

Para ativar o launcher nos `run.sh` do SMSForge neste usuário, crie `tools/emuladores/emulators.json` com a seleção abaixo. Se houver uma seleção local, preserve uma cópia e revise a mudança do emulador padrão.

```json
{
  "default_emulator": "tools/emuladores/emulicious/emulicious-deck",
  "emulicious_jar": "tools/emuladores/emulicious/Emulicious.jar"
}
```

Para abrir pelo menu, crie `smsforge-emulicious.desktop` em `$XDG_DATA_HOME/applications` (padrão `~/.local/share/applications`). Substitua `/caminho/do/SMSForge` pela raiz absoluta do checkout.

```ini
[Desktop Entry]
Type=Application
Name=Emulicious (SMSForge)
Exec="/caminho/do/SMSForge/tools/emuladores/emulicious/emulicious-deck" %f
Path=/caminho/do/SMSForge/tools/emuladores/emulicious
Icon=input-gaming
Terminal=false
Categories=Game;Emulator;
```

O launcher seleciona o Deck integrado como P1 no Master System, mantém o teclado habilitado e libera o modo desktop no encerramento. O teclado também atende a sessão quando outro aplicativo já controla o Deck. Para validar no novo host, abra uma ROM jogável, confira direcional, A, B e Start, feche o Emulicious e confirme o retorno do trackpad e dos atalhos no KDE. A sessão física de 21/11/2026 confirmou os sinais e a restauração do desktop. A ROM diagnóstica usada naquela sessão ficou estática, portanto a reação do jogo precisa de um ensaio com ROM interativa.
