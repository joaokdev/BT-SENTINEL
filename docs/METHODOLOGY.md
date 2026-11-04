# Metodologia e interpretação

## 1. Descoberta BLE

O scanner escuta anúncios Bluetooth Low Energy em modo passivo por meio do Bleak. Não estabelece conexão com periféricos e não executa leituras ou escritas GATT. Anúncios podem omitir campos, conter valores mutáveis ou utilizar endereços aleatorizados. Um dispositivo que não aparece durante uma janela de descoberta não está necessariamente ausente.

## 2. Descoberta via BlueZ no Linux

No Linux, o scanner pode iniciar a descoberta padrão do BlueZ por `bluetoothctl scan on`. O BlueZ controla os transportes disponíveis e pode apresentar anúncios LE e dispositivos BR/EDR, conforme o adaptador e a versão do sistema. Por isso, os resultados são rotulados como `BlueZ`, e não como prova de Bluetooth Classic exclusivamente. Essa operação emite tráfego normal de descoberta e não estabelece conexão nem pareamento. O Windows usa BLE passivo nesta versão. O backend macOS do Bleak não oferece modo passivo, portanto BLE é desabilitado no macOS para preservar essa propriedade.

## 3. Interpretação de RSSI

RSSI é uma observação de rádio afetada por antena, absorção pelo corpo, obstáculos, interferência, orientação e potência de transmissão. Os rótulos de sinal são apenas referências visuais amplas, não estimativas de distância nem achados de segurança.

## 4. Metadados dos dispositivos

Nomes, UUIDs de serviço, identificadores de fabricante e valores de potência de transmissão são metadados de anúncio. Esses valores não são declarações autenticadas de identidade e não demonstram que um serviço remoto está acessível, configurado de forma insegura ou vulnerável.

## 5. Auditoria do adaptador local

A auditoria consulta somente informações locais do sistema operacional. Alguns sistemas não expõem o estado de descoberta ou pareamento pela interface utilizada; nesses casos, o valor permanece como `unknown` e nunca é convertido silenciosamente para `no`.

## 6. Relatórios

O relatório HTML é gerado localmente. Valores fornecidos pelos dispositivos são escapados antes da inserção no HTML. O relatório apresenta observações e limitações declaradas, sem correspondência especulativa de CVEs.

## 7. Tratamento de evidências

Mantenha, fora do inventário de dispositivos, um registro da autorização, data/hora, escopo aprovado, detalhes do host e regras de retenção. Proteja inventários e relatórios porque identificadores e metadados Bluetooth podem ser sensíveis.
