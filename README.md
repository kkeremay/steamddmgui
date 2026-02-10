# Steam DDM GUI

## Overview

Steam DDM GUI is software designed for digital content preservation. It provides a graphical interface to interact with Steam content delivery systems using standard `.lua` and `.manifest` files. This tool facilitates the backup and preservation of owned digital content by leveraging open-source components for compatibility and offline usage.

This project integrates several preservation tools:
- **DepotDownloaderMod**: For retrieving content from steam depots.
- **Goldberg Emulator**: For running applications in an offline, preservation-friendly environment.
- **Steamless**: For unpacking executables to ensure long-term compatibility.

**Note**: This software is intended for use with content you legally own.

## Features

- **Drag & Drop Interface**: Easily load game manifest files (`.zip` containining `.lua` & `.manifest`).
- **Automated Processing**: Handles depot downloading, extraction, and file management.
- **Cross-Platform**: Works on Windows and Linux.
- **Integrated Tools**: Automatically applies Goldbeg emulator and Steamless unpacking where applicable.

---

## Part 1: Installation (Release)

Download the latest release from the [Releases](https://github.com/kkeremay/steamddmgui/releases) page.

### Linux Users
To use the Steamless feature on Linux, you must have Mono installed.
- Ubuntu/Debian: `sudo apt install mono-complete`
- Fedora: `sudo dnf install mono-complete`
- Arch: `sudo pacman -S mono`

### Usage

1.  Launch the application (`SteamDDMGUI` or `SteamDDMGUI.exe`).
2.  Select a download directory where the game files will be saved.
3.  Drag and drop a `.zip` file containing the game's `.lua` and `.manifest` files into the application window.
4.  Click **START DOWNLOAD**.
5.  Wait for the process to complete. The status bar will show progress.

---

## Part 2: Building from Source

If you prefer to compile the application yourself, follow these instructions.

### Prerequisites

- **Python**: 3.12 (Recommended for best compatibility with PyInstaller).
- **Mono** (Linux only): Required to run Steamless during development or testing.

### Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/kkeremay/steamddmgui.git
    cd SteamDDMGUI
    ```

2.  Install python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Ensure the following external binaries are present in the root directory:
    - `DepotDownloaderMod` (Linux) or `DepotDownloaderMod.exe` (Windows)
    - `goldberg/` directory containing `steam_api.dll` and `steam_api64.dll`
    - `steamless/` directory containing `Steamless.CLI.exe` and `Steamless.API.dll`

### Compilation

To compile the application into a standalone executable for distribution, use `pyinstaller`. The build process requires including the binary dependencies.

#### Windows

```powershell
pyinstaller --noconfirm --onefile --windowed --name "SteamDDMGUI" `
    --add-data "DepotDownloaderMod.exe;." `
    --add-data "goldberg;goldberg" `
    --add-data "steamless;steamless" `
    SteamDDMGUI.py
```

#### Linux

Ensure `DepotDownloaderMod` has execution permissions (`chmod +x DepotDownloaderMod`) before building.

```bash
pyinstaller --noconfirm --onefile --windowed --name "SteamDDMGUI" \
    --add-data "DepotDownloaderMod:." \
    --add-data "goldberg:goldberg" \
    --add-data "steamless:steamless" \
    SteamDDMGUI.py
```

The compiled executable will be located in the `dist/` directory.

### External Dependencies

This project requires `DepotDownloaderMod`. While compiled executables are included with the source code, you can compile it yourself from source. Please refer to the [DepotDownloaderMod GitHub Repository](https://github.com/SteamAutoCracks/DepotDownloaderMod) for build instructions.

## Legal Disclaimer

**Non-Affiliation:** This project is an independent, third-party utility. It is not affiliated with, authorized, maintained, sponsored, or endorsed by Valve Corporation, Steam, or any of its affiliates or subsidiaries. 

**Trademarks:** "Steam" and the Steam logo are trademarks or registered trademarks of Valve Corporation in the U.S. and/or other countries. All other trademarks are the property of their respective owners.

**Usage:** This software is intended for personal archival and educational purposes only. The developers assume no liability for misuse, account actions, or data loss resulting from the use of this tool.

## Acknowledgments & Third-Party Components

This software integrates the following tools to function:

-   **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)**: A modified version of DepotDownloader for retrieving depot content.
-   **[Steamless](https://github.com/Atom0s/Steamless)**: A DRM unpacker for SteamStub variants.
-   **Goldberg Emulator**: A lightweight Steam emulator for offline play.
