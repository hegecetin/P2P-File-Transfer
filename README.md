# P2P File Transfer

A Windows-friendly graphical interface for [Magic Wormhole](https://github.com/magic-wormhole/magic-wormhole), built with Python and Tkinter. The interface includes Turkish and English language settings, dark/light themes, transfer status, a persistent activity log, and separate receive folders to avoid overwriting existing files.

> **Status:** Source and Windows build pipeline are prepared. The GUI source can be syntax-checked and helper-tested on Python. The Windows `.exe` must be built on Windows (locally or by GitHub Actions); a live two-computer transfer test is still required before calling a release production-verified.

## Features

- Send a file or a folder using Magic Wormhole.
- Receive files using a one-time transfer code.
- Turkish / English interface and dark / light themes.
- Transfer status, progress, speed and elapsed-time display.
- Activity log stored under `%APPDATA%\KolayDosyaAktarimi` on Windows.
- Unique receive subfolders help protect existing files.
- Windows 10/11 single-file GUI executable build pipeline that bundles a standalone Magic Wormhole CLI.

## Run from source

Install Python 3.10+ and a working Tk/Tcl installation, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python p2p_file_transfer.py
```

The source-run version also needs the `wormhole` command available on `PATH` or in the active Python environment. The Windows release build bundles its own CLI executable.

## Build a single Windows executable

Build on Windows 10/11 with Python 3.12 installed:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

Output: `dist\P2PFileTransfer.exe`. The build uses PyInstaller twice: first to produce a standalone Magic Wormhole CLI, then to bundle it with the GUI. Since this is a networked file-transfer application, the generated executable should be tested on a clean Windows machine before distribution.

### GitHub Actions build

1. Create an empty GitHub repository.
2. Upload/push the contents of this folder to the repository's `main` branch.
3. Open **Actions → Windows build**.
4. Download the `P2PFileTransfer-Windows-x64` artifact from a successful workflow run.

The workflow runs the helper tests and produces the executable artifact. It does not automatically publish a GitHub Release.

## Tests

```powershell
python -m pip install -r requirements-build.txt
python -m pytest -q
python -m py_compile p2p_file_transfer.py
```

## Security and privacy notes

- Transfer codes are single-use; share them only with the intended recipient.
- Magic Wormhole coordinates the transfer using its relay infrastructure and may attempt direct connections. See the upstream project's documentation for protocol and network details.
- The local activity log can include file paths, transfer codes and error details. Review it before sharing logs publicly; avoid publishing personal data.
- Only receive files from people you trust and scan received files as appropriate.

## Project structure

```text
p2p-file-transfer-github/
├── .github/workflows/windows-build.yml
├── build_support/wormhole_cli.py
├── tests/test_helpers.py
├── p2p_file_transfer.py
├── requirements.txt
├── requirements-build.txt
├── build_windows.ps1
├── LICENSE
└── README.md
```

## Credits

The secure transfer protocol and CLI are provided by the Magic Wormhole project. This repository provides the Tkinter interface and Windows packaging workflow; it is not affiliated with the upstream project.
