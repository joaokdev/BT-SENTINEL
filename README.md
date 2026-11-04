# BT SENTINEL

Ferramenta educacional para observação e inventário de dispositivos Bluetooth em ambientes controlados. O projeto oferece uma interface de terminal para descoberta de dispositivos próximos, consulta local do adaptador e organização das observações em inventário e relatório HTML.

## Finalidade acadêmica e uso autorizado

O BT SENTINEL foi desenvolvido para fins educativos e acadêmicos, como apoio a aulas, laboratórios, demonstrações e estudos sobre descoberta Bluetooth, anúncios BLE, metadados de dispositivos e tratamento responsável de dados técnicos. Pode ser utilizado em atividades de ensino e pesquisa realizadas em equipamentos próprios, laboratórios isolados ou ambientes nos quais o operador tenha autorização explícita.

> **Autorização e privacidade:** antes de iniciar uma descoberta, obtenha autorização do responsável pelo ambiente. Dispositivos próximos podem pertencer a terceiros; nomes, identificadores, intensidade de sinal e dados de fabricante podem ser sensíveis. Colete apenas o necessário, mantenha os arquivos protegidos e remova-os quando deixarem de ser necessários. O uso da ferramenta não substitui a aprovação institucional ou as regras aplicáveis a uma atividade acadêmica.

## O que o projeto faz

- Apresenta um painel interativo no terminal para iniciar descobertas e consultar resultados.
- Observa anúncios Bluetooth Low Energy (BLE) de forma passiva em Windows e Linux compatíveis.
- No Linux, permite descoberta próxima de Bluetooth Classic por meio da consulta padrão de inquiry do BlueZ. Essa operação transmite sinais de descoberta, mas não estabelece conexão nem pareamento.
- Faz uma consulta local, somente leitura, ao estado e às informações disponíveis do adaptador Bluetooth.
- Mantém um inventário local com identificadores observados, metadados anunciados, primeira e última observação, contagem de observações e RSSI quando disponível.
- Gera um relatório HTML independente a partir do inventário.
- Registra eventos da sessão para apoiar a revisão do procedimento realizado.

O RSSI é uma indicação aproximada da intensidade do sinal e não permite determinar com precisão a distância. Identificadores, UUIDs e dados de fabricante são observações; isoladamente, não comprovam identidade, propriedade, vulnerabilidade ou exposição de um serviço.

## Escopo e limitações

| Recurso | Windows | Linux | macOS |
| --- | --- | --- | --- |
| Descoberta passiva de anúncios BLE | Sim, conforme adaptador e permissões | Sim, conforme adaptador e permissões | Não incluída |
| Descoberta Bluetooth Classic | Não incluída | Sim, via BlueZ | Não incluída |
| Auditoria local do adaptador | Inventário Bluetooth PnP | Estado via `bluetoothctl show` | Consulta básica via `system_profiler` |
| Interface de terminal e relatórios HTML | Sim | Sim | Sim, com recursos de rádio limitados |

A disponibilidade depende do sistema operacional, do adaptador, dos drivers, das permissões e do estado do serviço Bluetooth. No Windows, o identificador BLE pode ser específico do sistema e não corresponder a um endereço MAC. O backend macOS do Bleak não oferece o modo passivo usado pelo projeto, por isso a descoberta BLE não é habilitada nesse sistema.

A ferramenta não realiza conexão a dispositivos descobertos, enumeração de serviços remotos, pareamento forçado, tentativa de PIN, escrita GATT, spoofing, exploração de vulnerabilidades, interferência ou negação de serviço. A auditoria do adaptador local é somente leitura.

## Requisitos

- Python 3.10 ou superior.
- Adaptador Bluetooth compatível para executar atividades de descoberta.
- No Linux, BlueZ e `bluetoothctl` para a descoberta Classic.
- No Windows, PowerShell para consultar o inventário local de dispositivos Bluetooth durante a auditoria.

É possível abrir a interface e consultar funcionalidades sem hardware compatível, mas a descoberta de rádio depende do adaptador e da configuração do sistema.

## Como instalar e iniciar

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/joaokdev/BT-SENTINEL.git
cd BT-SENTINEL
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m bt_sentinel
```

Se a política local bloquear a ativação do ambiente virtual, permita scripts apenas na janela atual do PowerShell e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Como alternativa, o script `scripts/setup_windows.ps1` prepara o ambiente e `scripts/start_windows.bat` inicia a aplicação.

### Linux (Debian, Ubuntu e Kali)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip bluez
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m bt_sentinel
```

Como alternativa, use `bash scripts/setup_linux.sh` para preparar o ambiente e `bash scripts/start_linux.sh` para iniciar a aplicação. Para descoberta Classic, verifique se o serviço BlueZ e o adaptador estão disponíveis. Use somente as permissões necessárias no ambiente autorizado.

### macOS

As dependências Python e a interface podem ser instaladas pelo mesmo fluxo de ambiente virtual usado no Linux. A descoberta BLE passiva e a descoberta Classic não estão incluídas no macOS; portanto, o uso nesse sistema fica limitado às funções compatíveis, como interface, inventário, relatórios e consulta local documentada.

## Utilização

O comando abaixo abre o painel interativo:

```bash
python -m bt_sentinel
```

No painel, selecione **Live discovery**, defina a duração e o transporte disponíveis e acompanhe os resultados. Ao selecionar um dispositivo, a aplicação exibe os metadados observados. Consulte o inventário ou gere o relatório HTML pelo próprio painel.

Também é possível usar os comandos da linha de comando. Cada operação solicita confirmação explícita de autorização:

```bash
# Descoberta BLE e Classic quando disponíveis, por 20 segundos
python -m bt_sentinel scan --duration 20 --transport all

# Somente anúncios BLE
python -m bt_sentinel scan --duration 20 --transport ble

# Somente Classic (Linux com BlueZ)
python -m bt_sentinel scan --duration 20 --transport classic

# Consultar o inventário, auditar o adaptador ou gerar relatório
python -m bt_sentinel inventory
python -m bt_sentinel audit
python -m bt_sentinel report
```

A duração aceita pela aplicação é limitada ao intervalo de 5 a 120 segundos. Para interromper uma descoberta, pressione `Ctrl+C`.

## Dados gerados

Quando executada na pasta do projeto, a aplicação mantém os dados localmente em `data/`, os relatórios em `reports/` e os registros de sessão em `logs/`. Os arquivos podem incluir identificadores e metadados observados; revise-os antes de compartilhar. Fora da pasta do projeto, os dados são armazenados em `~/.bt-sentinel/` (no perfil do usuário no Windows). Arquivos de dados, relatórios e logs locais são excluídos do controle de versão pelo `.gitignore`.

## Estrutura

```text
bt_sentinel/   implementação da aplicação
data/          inventário e auditoria locais
docs/          arquitetura, metodologia e limites de segurança
logs/          registros locais de sessão
reports/       relatórios HTML gerados
scripts/       instalação e inicialização
tests/         testes automatizados
```

## Referências e documentação

Consulte `docs/METHODOLOGY.md` para informações sobre o método de observação, `docs/ARCHITECTURE.md` para a organização interna, `docs/SECURITY_BOUNDARIES.md` para os limites de uso e `docs/REFERENCES.md` para referências técnicas.

## Aviso

O BT SENTINEL é um recurso de aprendizagem e observação defensiva. Não substitui avaliação profissional, documentação do fabricante nem revisão ética, institucional ou jurídica de uma pesquisa. O operador é responsável pela autorização, pelo escopo da atividade e pela proteção dos dados coletados.
