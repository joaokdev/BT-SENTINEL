# Referências técnicas

Documentação oficial consultada para compatibilidade e comportamento das bibliotecas:

- Bleak 3.0.2 — API `BleakScanner`: https://bleak.readthedocs.io/en/latest/api/scanner.html
- Bleak 3.0.2 — backend Windows: https://bleak.readthedocs.io/en/latest/backends/windows.html
- Bleak 3.0.2 — backend Linux / BlueZ: https://bleak.readthedocs.io/en/latest/backends/linux.html
- Bleak — pacote e versões publicadas: https://pypi.org/project/bleak/
- Rich — pacote e versões publicadas: https://pypi.org/project/rich/

O modo passivo do scanner foi selecionado explicitamente para os backends Windows e Linux. O backend macOS não suporta o modo passivo do Bleak; por essa razão, a descoberta BLE nesse sistema não está habilitada neste projeto.
