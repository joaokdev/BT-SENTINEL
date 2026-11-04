# Limites de segurança

O BT SENTINEL foi projetado para observação BLE passiva, consulta Bluetooth Classic padrão sem conexão e revisão defensiva local.

### Incluído

- Escuta de anúncios BLE.
- Descoberta Bluetooth Classic no Linux por meio das ferramentas locais BlueZ.
- Consultas somente leitura do adaptador Bluetooth local.
- Inventário JSON local e geração de relatório HTML.

### Excluído por projeto

- Pareamento forçado, tentativa de PIN ou bypass de autenticação.
- Escritas GATT, alterações remotas de configuração ou enumeração de serviços remotos.
- Injeção de áudio, tomada de controle de mídia ou controle de dispositivos.
- Spoofing de MAC, interferência de rádio, flooding ou negação de serviço.
- Execução de exploits, entrega de payloads, persistência ou coleta de credenciais.

### Checklist de operação segura

1. Obtenha autorização explícita antes de iniciar a descoberta.
2. Execute varreduras em laboratório controlado ou área física aprovada.
3. Mantenha a duração no mínimo necessário.
4. Revise inventário e relatórios antes de compartilhá-los.
5. Exclua os dados coletados ao final do prazo de retenção aprovado.
6. Trate campos desconhecidos ou ausentes como desconhecidos, não como evidência de segurança.
