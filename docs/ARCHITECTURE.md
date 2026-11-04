# Arquitetura 4.0

- `scanner.py`: descoberta passiva BLE e descoberta padrão BlueZ no Linux.
- `device_intel.py`: classificação heurística de família, confiança e evidências.
- `core.py`: normalização, consolidação, persistência e relatório HTML.
- `audit.py`: consultas locais somente de leitura do adaptador.
- `system_control.py`: abre configurações nativas de pareamento/áudio, players padrão e comandos de mídia locais.
- `ui.py`: menu Rich em português, painel de descoberta, inventário, check-up, pareamento e central de áudio.
- `cli.py`: entrada interativa e subcomandos.

Os módulos de pareamento e áudio não fazem conexão Bluetooth por endereço. O pareamento é delegado à interface do sistema e o áudio usa a sessão/saída padrão do computador.
