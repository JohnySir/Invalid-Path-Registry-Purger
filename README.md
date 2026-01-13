# 🗑️ Invalid Path Registry Purger

<div align="center">

![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A specialized system utility that identifies and removes orphaned ARP (Add/Remove Programs) registry entries pointing to non-existent file paths.**

[Technical Overview](#-technical-overview) • [Installation](#-installation) • [Usage](#-usage) • [Safety Architecture](#-safety-architecture)

</div>

---

## 🧐 What is this?

When software is manually deleted or an uninstallation fails, the Windows Registry often retains a record of the application in the **"Installed Apps"** list. In database terms, these are **"Orphaned Records"**—registry keys that point to an **Invalid Path**.

**Invalid Path Registry Purger** scans the `HKLM` and `HKCU` uninstall keys, verifies the existence of `InstallLocation` and `UninstallString` paths, and allows for the safe removal of these dead entries.

## ⚙️ Technical Overview

*   **🔍 Path Integrity Scan**: validates registry keys against the filesystem.
    *   Checks `InstallLocation` for directory existence.
    *   Parses and verifies `UninstallString` executables.
*   **🛡️ Registry Safety Layer**: 
    *   **Atomic Backups**: Automatically exports the target registry subkey to a `.reg` file before deletion.
    *   **Restore Capability**: Built-in history viewer to re-import deleted keys via `reg import`.
*   **⚠️ Force Purge**: (Advanced) Allows override for valid entries, removing the registry reference without triggering the uninstaller (useful for broken installers).
*   **🚫 System Protection**: Hard-coded exclusions for `SystemComponent` flags and HAL (Hardware Abstraction Layer) drivers to prevent OS destabilization.
*   **⚡ Optimized UI**: High-performance, debounced search filtering capable of handling large registry datasets.

## 🚀 Installation

### Prerequisites
*   Windows 10 or 11
*   Python 3.10 or newer

### Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/invalid-path-registry-purger.git
    cd invalid-path-registry-purger
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Usage

1.  **Run the application**:
    ```bash
    python main.py
    ```
    *Note: The process will auto-request **Administrator privileges** via UAC to access HKLM registry hives.*

2.  **Scan & Purge**:
    *   **Red Entries**: Identified as **"Ghosts"** (Invalid Path). Safe to remove.
    *   **Green Entries**: Valid installations.
    *   **Orange Entries**: System/Protected components (Hidden by default).

3.  **Advanced Operations**:
    *   **"Ghosts Only" Mode**: Toggle to filter the view to only show integrity violations.
    *   **Force Del**: Bypass safety checks to remove a valid entry (Registry Only). *Use with caution.*

## 🛡️ Safety Architecture

This tool operates on the principle of **Non-Destructive Filesystem Operations**:
1.  **Registry Only**: It never deletes program files, only the registry pointers.
2.  **Backup-First Logic**: Deletion operations are blocked until a backup verification passes.
3.  **HAL/Kernel Protection**: Logic explicitly ignores strings containing "Hardware Abstraction Layer" to prevent driver corruption.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss the proposed logic modification.

1.  Fork the project
2.  Create your feature branch (`git checkout -b fix/registry-logic`)
3.  Commit your changes (`git commit -m 'Refactor scanning algorithm'`)
4.  Push to the branch (`git push origin fix/registry-logic`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
<i>"Clean Registry, Stable System."</i>
</div>
