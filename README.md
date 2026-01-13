# 🧹 Uninstall Cleaner

<div align="center">

![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A modern, safe, and powerful utility to remove "Ghost" entries from your Windows Installed Apps list.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Safety](#-safety-first)

</div>

---

## 🧐 What is this?

Have you ever manually deleted a program folder, only to find it still lurking in your Windows "Add or Remove Programs" list? Or had an uninstaller fail, leaving a broken entry behind?

**Uninstall Cleaner** is the solution. It detects these **"Ghost"** entries—registry records pointing to files that no longer exist—and helps you remove them safely.

## ✨ Features

*   **👻 Ghost Detection Engine**: Automatically scans your registry and identifies programs missing their installation files or uninstallers.
*   **🛡️ Safety First**: 
    *   **Auto-Backup**: Every removal triggers an automatic `.reg` file backup.
    *   **Undo History**: Made a mistake? Restore deleted entries instantly from the app.
*   **⚠️ Force Remove**: (Advanced) Clean up valid but stubborn entries that standard uninstallers can't remove.
*   **🔍 Smart Search**: Real-time filtering with a smooth, optimized UI (debounced for performance).
*   **🌗 Modern UI**: Built with `customtkinter` for a native Windows 11-style look with Dark Mode support.
*   **🛡️ System Protection**: Automatically hides critical system components and hardware drivers (HAL) to prevent accidental damage.

## 🚀 Installation

### Prerequisites
*   Windows 10 or 11
*   Python 3.10 or newer

### Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/uninstall-cleaner.git
    cd uninstall-cleaner
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
    *Note: The app will request **Administrator privileges**. This is required to modify the Windows Registry (HKLM).*

2.  **Scan & Clean**:
    *   The app launches and scans for installed software.
    *   **Red items** are "Ghosts" (broken).
    *   **Green items** are Valid (installed).
    *   Click **"Remove"** on a Ghost to clean it up.

3.  **Advanced Options**:
    *   Toggle **"Ghosts Only"** in the sidebar to filter the list.
    *   Use **"Force Del"** on valid apps (Proceed with caution! This removes the registry entry, not the files).

## 🛡️ Safety First

We take system stability seriously:
1.  **Backups**: Before *any* deletion, a backup is saved to the `backups/` folder.
2.  **Filtering**: Critical system components and drivers (e.g., "Hardware Abstraction Layer") are hidden from the list.
3.  **Confirmation**: You will always be asked to confirm before any action is taken.

## 🤝 Contributing

Contributions are welcome!
1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
Made with ❤️ for Windows
</div>
