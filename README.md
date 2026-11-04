# BT SENTINEL 4.0.0

**Central de Inteligência Bluetooth · PAI JOÃO K DEV**

O BT SENTINEL é um projeto educacional para descoberta Bluetooth autorizada, organização de inventário, classificação heurística de dispositivos, check-up local do adaptador e integração com os controles de pareamento e áudio do próprio sistema operacional.

> **Uso autorizado.** Utilize somente equipamentos seus ou ambientes em que você tenha autorização explícita. A aplicação não invade, não contorna pareamento e não assume o controle de dispositivos encontrados. O pareamento ocorre na interface oficial do Windows/Linux, com confirmação do operador e do dispositivo.

## Novidades da versão 4.0

- Interface de terminal inteiramente em português, com assinatura visual **PAI JOÃO K DEV**.
- Menu simplificado: descoberta, inteligência/inventário, check-up, pareamento, central de áudio, relatórios e ajuda.
- Tabela de descoberta ao vivo, com atualização enquanto a busca está em andamento.
- Classificação provável de famílias de dispositivos (fone/headset, caixa de som, smartphone, smartwatch, computador, TV, controle, HID, impressora, sensor/IoT ou não identificado).
- A classificação informa nível de confiança e evidências. É heurística, pode errar e não afirma modelo, dono ou vulnerabilidade.
- Fluxo de pareamento que abre as configurações Bluetooth oficiais do sistema; o usuário seleciona o dispositivo e confirma o pareamento no sistema e no próprio aparelho.
- Central de áudio que abre as configurações de saída, abre arquivo de áudio local ou página HTTPS do YouTube e envia comandos de mídia/volume à sessão ou saída padrão do computador.
- Registros de auditoria e relatórios mantidos localmente.
- Mensagens de interface e documentação em português.

## O que cada módulo realmente faz

| Módulo | O que faz | Limite importante |
|---|---|---|
| Descobrir dispositivos | Observa anúncios BLE e, no Linux, pode usar descoberta BlueZ | Não conecta nem pareia os encontrados |
| Inteligência / inventário | Classifica por nome/UUID observado e guarda histórico | A classificação é uma hipótese, não identificação forense |
| Check-up | Consulta informações do adaptador local | No Windows, a consulta PnP não prova por si só que o rádio está ligado |
| Parear dispositivo | Abre a tela Bluetooth oficial do sistema | O ID de rádio não é senha/chave de acesso; pareamento exige confirmação normal |
| Central de áudio | Abre seletor de saída, reproduz arquivo/YouTube no player/navegador padrão e controla a sessão local | Os controles não são enviados para um endereço Bluetooth específico; atuam na sessão/saída padrão do PC |
| Relatório | Gera HTML com dados do inventário e check-up local | Não é laudo de vulnerabilidade |

## Compatibilidade por plataforma

| Recurso | Windows 10/11 | Kali Linux / Linux com BlueZ |
|---|---:|---:|
| Interface interativa em português | Sim | Sim |
| Descoberta BLE passiva | Sim, adaptador/driver compatível | Sim, adaptador/BlueZ compatível |
| Descoberta por BlueZ | Não | Sim, `bluetoothctl`; resultado pode incluir LE e BR/EDR |
| Classificação heurística | Sim | Sim |
| Check-up local do adaptador | Inventário Bluetooth PnP | `bluetoothctl show` |
| Abrir tela oficial de pareamento | Configurações do Windows | Blueman / GNOME / KDE, se instalado |
| Abrir configuração de saída de áudio | Configurações de Som do Windows | pavucontrol / GNOME / KDE, se instalado |
| Play/Pause/Next/Previous | Teclas multimídia do Windows | `playerctl` |
| Volume / mute | Teclas multimídia do Windows | `wpctl` (PipeWire) ou `pactl` (PulseAudio) |

A disponibilidade real depende do adaptador, driver, versão do sistema, permissões e ambiente gráfico. Em Windows, o identificador BLE entregue pelo sistema pode ser um identificador interno em vez de um MAC físico.

## Pareamento e áudio: fluxo correto

1. Execute uma descoberta e encontre o dispositivo que você reconhece como seu.
2. Abra **Parear dispositivo** e selecione o item do inventário.
3. Confirme que o aparelho é seu/autorizado. O programa abrirá as configurações nativas do sistema.
4. Na tela do Windows/Linux, selecione o dispositivo e confirme o pareamento; confira o mesmo PIN/código nos dois lados, quando solicitado.
5. Abra **Central de áudio** e escolha a saída Bluetooth nas configurações de som do sistema.
6. Abra um arquivo local compatível ou uma página HTTPS do YouTube. O navegador/player usa a saída padrão selecionada.
7. Use Play/Pause/Próxima/Anterior e volume. Esses comandos atuam sobre a sessão de mídia/saída padrão do computador.

**Importante:** não existe função “conectar pelo MAC e tomar controle”. O endereço/ID serve para reconhecer registros da descoberta. A aplicação não transmite áudio diretamente por um protocolo Bluetooth privado nem contorna autenticação.

## Requisitos

- Python 3.10 ou superior.
- Adaptador Bluetooth com suporte BLE para descoberta BLE.
- Linux: BlueZ/`bluetoothctl` para descoberta pelo serviço Bluetooth do sistema.
- Linux: `playerctl` para controles de faixa; `wpctl` (PipeWire) ou `pactl` (PulseAudio) para volume.
- Windows: Bluetooth habilitado e driver funcional; os controles usam as teclas multimídia do sistema.

## Instalação no Windows

Abra o PowerShell na pasta extraída:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Inicie:

```powershell
.\scripts\start_windows.bat
```

Ou, com o ambiente virtual ativado:

```powershell
python -m bt_sentinel
```

### Gerar um executável `.exe` (no próprio Windows)

O ZIP contém o código-fonte e o script de compilação; o `.exe` não é pré-compilado neste pacote. No Windows, depois da instalação, execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

O resultado esperado é `dist\BT-SENTINEL.exe`. A compilação deve ser validada no Windows com o adaptador e os drivers que serão usados. O executável não inclui drivers Bluetooth do fabricante nem concede acesso a dispositivos sem pareamento normal.

## Instalação no Kali Linux / Debian / Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip bluez playerctl
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Opcional para volume em PipeWire: instale `wireplumber`/`wpctl`. Em sistemas PulseAudio, use `pactl`.

Inicie:

```bash
python -m bt_sentinel
```

Scripts de conveniência:

```bash
bash scripts/setup_linux.sh
bash scripts/start_linux.sh
```

## Uso do painel

1. Confirme que usará o programa em dispositivos/ambientes autorizados.
2. Escolha **1 · Descobrir dispositivos**.
3. Defina de 5 a 120 segundos. No Windows, a descoberta disponível é BLE. No Linux, você pode escolher BLE, descoberta BlueZ ou ambos.
4. Observe a tabela ao vivo e, ao concluir, selecione um item para ver a ficha.
5. Use **2 · Inteligência / inventário** para inspecionar registros salvos.
6. Use **3 · Check-up** para verificar o adaptador local.
7. Use **4 · Parear dispositivo** para abrir as configurações nativas.
8. Depois do pareamento, use **5 · Central de áudio** para selecionar a saída, abrir áudio e controlar a sessão do PC.

## Comandos de terminal

```bash
# Painel interativo
python -m bt_sentinel

# Descoberta BLE por 20 segundos
python -m bt_sentinel scan --duration 20 --transport ble

# Descoberta BLE + BlueZ no Linux
python -m bt_sentinel scan --duration 20 --transport all

# Check-up local
python -m bt_sentinel audit

# Gerar relatório HTML
python -m bt_sentinel report
```

## Estrutura

```text
BT_SENTINEL_4.0.0/
├── bt_sentinel/
│   ├── audit.py             # check-up local de adaptador
│   ├── cli.py               # entrada CLI
│   ├── core.py              # inventário, parsing e relatório
│   ├── device_intel.py      # classificação heurística de dispositivos
│   ├── scanner.py           # descoberta BLE e BlueZ
│   ├── system_control.py    # abertura de configurações e mídia local
│   └── ui.py                # interface Rich em português
├── data/                    # inventário e check-up local
├── docs/                    # arquitetura, metodologia e limites
├── logs/                    # trilha local de auditoria
├── reports/                 # relatórios HTML
├── scripts/                 # instalação e inicialização
├── tests/                   # testes automatizados
├── pyproject.toml
└── requirements.txt
```

## Dados e privacidade

- `data/inventory.json`: nomes, identificadores, RSSI, UUIDs e horários observados.
- `data/adapter_audit.json`: informações consultadas do adaptador local.
- `logs/audit.jsonl`: operações realizadas na sessão.
- `reports/relatorio_bt_sentinel.html`: relatório gerado.
- Os arquivos são locais. Revise os identificadores antes de compartilhar qualquer relatório.

## Limites de segurança

O BT SENTINEL não implementa exploração, invasão, bypass de pareamento, adivinhação de PIN, captura de credenciais, escrita GATT, tomada de controle remota, injeção de áudio, spoofing de endereço, flooding, interferência ou negação de serviço.

A descoberta não prova que um dispositivo está vulnerável ou disponível para conexão. RSSI não é uma medição confiável de distância. Nome, UUID e fabricante podem ser incompletos ou falsificados. A classificação de família é heurística e deve ser tratada como pista visual, não evidência conclusiva.

O módulo de áudio opera por meio da sessão e da saída padrão do próprio computador. O pareamento é tratado pelo sistema operacional. Isso preserva o mecanismo normal de autenticação e autorização Bluetooth.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes automatizados não exigem hardware Bluetooth real. Eles verificam parsing, classificação, inventário, interface e limites dos controles locais com dependências simuladas. A descoberta física precisa ser validada no notebook/adaptador do operador.

## Aviso educacional

Este repositório é um projeto educacional de observabilidade Bluetooth e gerenciamento local de mídia. Ele não substitui uma avaliação profissional, documentação do fabricante ou aconselhamento jurídico. O operador é responsável por obter autorização, proteger os dados coletados e respeitar as regras aplicáveis.
