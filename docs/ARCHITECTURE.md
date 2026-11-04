# Visão da arquitetura

| Módulo | Responsabilidade |
|---|---|
| `cli.py` / `__main__.py` | Entrada do processo e interpretação de comandos |
| `ui.py` | Painel Rich, tabela em tempo real, seleção e fluxo do operador |
| `scanner.py` | Callback de anúncios BLE e descoberta Classic via BlueZ no Linux |
| `audit.py` | Consultas locais e somente leitura do adaptador por plataforma |
| `core.py` | Normalização, consolidação, persistência JSON atômica e geração HTML |
| `tests/` | Testes offline de parsing, consolidação, persistência e segurança do relatório |

Os callbacks de descoberta enviam observações para a interface. A interface consolida as observações em uma visão de sessão e atualiza o inventário cumulativo. O gerador de relatórios recebe dados estruturados locais e escapa os valores no ponto de inserção do HTML.
