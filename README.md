# BT SENTINEL 

O BT SENTINEL é um projeto educacional voltado ao aprendizado de descoberta de ativos Bluetooth, descoberta BLE passiva, revisão da configuração local do adaptador e geração de relatórios. A interface funciona diretamente no terminal, com painel em tempo real e seleção de dispositivos após a descoberta.

> **Uso somente autorizado.** Execute a ferramenta apenas em equipamentos próprios ou em ambientes nos quais você tenha autorização explícita. Nomes, identificadores e dados de fabricante Bluetooth podem ser informações sensíveis. Colete somente o necessário e proteja os arquivos gerados.



- Painel interativo no terminal com atualização em tempo real.
- Seleção de um dispositivo encontrado e visualização dos metadados observados.
- Descoberta passiva de anúncios Bluetooth Low Energy (BLE) por meio do Bleak em Windows e Linux compatíveis.
- Descoberta Bluetooth Classic próxima por meio do BlueZ `bluetoothctl` no Linux.
- Auditoria local e somente leitura do adaptador Bluetooth, com suporte específico por sistema operacional.
- Inventário JSON persistente, horários da primeira e última observação, estimativa visual de RSSI e contagem de observações.
- Relatório HTML independente, com valores recebidos dos dispositivos escapados antes de serem inseridos no HTML.
- Separação entre observações e conclusões de segurança. A ferramenta não cria correlações especulativas de CVE com base em nome, endereço, RSSI ou UUID anunciado.
- Testes automatizados para parsing, consolidação do inventário, serialização e segurança do relatório.

## Matriz de compatibilidade

| Recurso | Windows | Linux | macOS |
|---|---:|---:|---:|
| Descoberta passiva de anúncios BLE | Sim, com adaptador/permissões compatíveis | Sim, com adaptador/permissões compatíveis | Não incluída |
| Descoberta próxima Bluetooth Classic | Não incluída | Sim, via BlueZ | Não incluída |
| Auditoria local do adaptador | Inventário Bluetooth PnP | Estado via `bluetoothctl show` | Consulta básica via `system_profiler` |
| Interface interativa no terminal | Sim | Sim | Sim |
| Relatório HTML | Sim | Sim | Sim |

Permissões do sistema operacional, drivers, hardware e estado do Bluetooth podem afetar a descoberta. O modo passivo do Bleak é suportado nos backends Windows e Linux, mas não no backend macOS; por isso, o projeto não habilita BLE no macOS para manter a operação BLE passiva. No Windows, o identificador BLE pode ser específico do sistema operacional, em vez de um endereço MAC. O inventário preserva esse identificador sem apresentá-lo incorretamente como MAC físico.

## Requisitos

- Python 3.10 ou superior.
- Adaptador Bluetooth com suporte BLE para descoberta BLE.
- No Linux, BlueZ e `bluetoothctl` para descoberta Bluetooth Classic. Essa consulta transmite os pacotes padrão de inquiry e não estabelece conexão nem pareamento.
- No Windows, o PowerShell é utilizado somente para consultar o inventário local de dispositivos Bluetooth Plug-and-Play durante a auditoria do adaptador.

## Instalação no Windows

Abra o PowerShell na pasta extraída do projeto:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Caso o PowerShell bloqueie a ativação do ambiente virtual, permita a execução somente na janela atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Inicie o painel:

```powershell
python -m bt_sentinel
```

Também há scripts de conveniência na pasta `scripts/`. Para instalar automaticamente:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Depois, inicie o painel com:

```powershell
.\scripts\start_windows.bat
```

Após a instalação editável, também é possível iniciar pelo comando `bt-sentinel`.

## Instalação no Kali Linux / distribuições baseadas em Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip bluez
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Inicie o painel:

```bash
python -m bt_sentinel
```

Como alternativa, use `bash scripts/setup_linux.sh` para preparar o ambiente virtual e `bash scripts/start_linux.sh` para iniciar o painel.

Para descoberta Classic, confirme que o serviço Bluetooth e o adaptador estão disponíveis. Algumas configurações Linux exigem permissões adequadas ou que a descoberta seja executada em uma sessão administrativa autorizada. Não execute a aplicação inteira como root, a menos que a configuração do seu sistema realmente exija isso.

## Comandos rápidos

A interface interativa é a forma recomendada de utilizar o projeto. Todos os comandos solicitam confirmação explícita de autorização.

```bash
# Painel interativo
python -m bt_sentinel

# BLE + Classic onde houver suporte, durante 20 segundos
python -m bt_sentinel scan --duration 20 --transport all

# Somente BLE
python -m bt_sentinel scan --duration 20 --transport ble

# Somente Classic (Linux / BlueZ)
python -m bt_sentinel scan --duration 20 --transport classic

# Consultar inventário salvo
python -m bt_sentinel inventory

# Auditoria local, somente leitura
python -m bt_sentinel audit

# Gerar relatório HTML
python -m bt_sentinel report
```

A duração da descoberta é limitada a 5–120 segundos. Pressione `Ctrl+C` para interromper a varredura. Ao final, informe o número de uma linha para inspecionar o dispositivo ou pressione Enter para pular.

## Fluxo pela interface

1. Abra o painel e confirme que possui autorização.
2. Entre em **Live discovery**.
3. Escolha a duração e os transportes.
4. Observe os dispositivos surgindo e sendo atualizados na tabela.
5. Selecione uma linha para ver nome, endereço/identificador observado, RSSI, UUIDs anunciados, IDs de fabricante e horários.
6. Consulte o inventário salvo ou gere um relatório HTML.

RSSI é apenas uma estimativa grosseira do sinal de rádio. Não representa uma medição confiável de distância. UUIDs anunciados e dados de fabricante são observações, não provas de que um serviço está acessível ou vulnerável.

## Estrutura do projeto

```text
BT_SENTINEL_3.0/
├── bt_sentinel/
│   ├── __init__.py
│   ├── __main__.py
│   ├── audit.py          # auditoria local, somente leitura
│   ├── cli.py            # ponto de entrada da CLI
│   ├── core.py           # inventário, parsing, persistência e relatórios
│   ├── scanner.py        # descoberta BLE e Classic no Linux
│   └── ui.py             # painel interativo no terminal
├── data/                 # inventário JSON e auditoria local
├── docs/                 # metodologia e limites de segurança
├── logs/                 # trilha de auditoria local em JSON Lines
├── reports/              # relatórios HTML gerados
├── scripts/              # instalação e inicialização no Windows e Linux
├── tests/                # testes automatizados
├── pyproject.toml
└── requirements.txt
```

## Dados e privacidade

- `data/inventory.json` armazena as observações de dispositivos encontrados.
- `data/adapter_audit.json` armazena a fotografia da configuração local do adaptador.
- `reports/assessment.html` é um relatório independente.
- `logs/audit.jsonl` registra eventos da sessão, sem armazenar o conteúdo dos anúncios de dispositivos.
- Quando executado fora da pasta do projeto, o inventário e os relatórios ficam em `~/.bt-sentinel/` (no Windows, dentro do perfil do usuário).
- Os arquivos ficam armazenados localmente. Revise identificadores e metadados antes de compartilhar qualquer inventário ou relatório.
- O `.gitignore` evita incluir inventários, dados de auditoria, relatórios, ambientes virtuais e logs no controle de versão.

## Limites de segurança

O BT SENTINEL realiza escuta passiva de anúncios BLE em Windows e Linux. No Linux, a descoberta Bluetooth Classic utiliza a consulta padrão de inquiry, que emite transmissões de descoberta, sem estabelecer conexão nem pareamento. A auditoria do adaptador local é somente leitura. A aplicação não se conecta a dispositivos descobertos nem realiza enumeração de serviços remotos.

Por projeto, a ferramenta **não inclui** pareamento forçado, ataques a PIN, escrita GATT, injeção de áudio, spoofing de endereço, execução de exploits, flooding de rádio, interferência, negação de serviço, persistência, coleta de credenciais ou alterações remotas de configuração.

A ferramenta não determina propriedade de dispositivos, identidade de usuários, possibilidade de exploração ou aplicabilidade de CVEs. Conclusões de segurança exigem inventário confiável de ativos, versões verificadas de sistema/firmware/stack, avisos do fabricante e um processo de avaliação aprovado separadamente.

## Testes

Execute a suíte na pasta do projeto:

```bash
python -m unittest discover -s tests -v
```

Os testes não exigem hardware Bluetooth nem uma descoberta de rádio ativa.

## Aviso educacional

Este repositório é um projeto educacional e de segurança defensiva. Seu propósito é apoiar conscientização sobre Bluetooth, descoberta BLE passiva, consulta Classic padrão autorizada e revisão de configurações locais e aprendizagem em ambientes controlados. Não substitui um teste de intrusão profissional, um aviso de segurança do fabricante ou orientação jurídica. O operador é responsável por obter autorização, proteger os dados coletados e cumprir as regras aplicáveis.
#   B T - S E N T I N E L  
 #   B T - S E N T I N E L  
 