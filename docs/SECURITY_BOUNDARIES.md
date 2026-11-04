# Limites de segurança e modelo operacional

BT SENTINEL 4.0 é uma ferramenta educacional de descoberta autorizada e controle de mídia local.

## Operações permitidas pelo projeto

- Escutar anúncios BLE em modo passivo onde o backend e o adaptador suportarem.
- Acionar a descoberta padrão do BlueZ no Linux.
- Registrar somente metadados observados e a configuração do adaptador local.
- Classificar prováveis famílias de dispositivos com base em nome/UUIDs anunciados, informando incerteza.
- Abrir a tela Bluetooth oficial do sistema operacional para pareamento normal.
- Controlar a sessão local de mídia/volume e selecionar saída pelo sistema operacional.

## Não implementado

- Pareamento forçado, PIN bypass, exploração ou acesso remoto.
- Conexão automática a aparelhos encontrados.
- Escrita GATT, alteração de firmware/configuração de terceiros, injeção de áudio ou tomada de controle.
- Spoofing, flooding, interferência, jamming ou DoS.

## Garantias e limitações

O identificador Bluetooth é metadado de observação e não uma credencial. Controles de mídia são emitidos ao sistema operacional e afetam sua sessão/saída padrão, não um alvo remoto escolhido por MAC. A classificação é heurística, e os registros podem estar incompletos ou ser aleatorizados.
