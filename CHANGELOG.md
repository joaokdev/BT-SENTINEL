# Changelog

## 3.0.0 — Terminal Control Center

- Replaced the command-only workflow with a Rich terminal dashboard.
- Added live BLE advertisement updates and post-scan device selection.
- Added passive BLE scanning mode on supported Windows and Linux backends.
- Added Linux-only Bluetooth Classic inquiry through BlueZ.
- Added read-only local adapter snapshots for Windows, Linux, and macOS.
- Added cumulative JSON inventory, structured audit events, and self-contained HTML reports.
- Removed generic CVE guesses that were not supported by verified device-version evidence.
- Added Windows and Linux setup/start helper scripts.
- Added offline unit tests for parsing, scanning-mode selection, inventory, audit logs, and report escaping.
