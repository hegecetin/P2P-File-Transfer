# P2P File Transfer

A lightweight peer-to-peer file transfer application built with Python, Tkinter, and Magic Wormhole.

Transfer files between devices using secure, code-based connections without manually configuring ports or sharing IP addresses.

## Features

- **Peer-to-peer transfers** — Send and receive files between devices.
- **Magic Wormhole** — Connect devices using a shared, automatically generated transfer code.
- **Graphical user interface** — Simple desktop interface built with Tkinter.
- **Cross-version compatibility** — Designed for supported Python versions on Windows.
- **No executable required** — Run the application directly from its Python source code.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer, subject to dependency compatibility
- The dependencies listed in `requirements.txt`

## Installation

**1. Install Python**

Download Python from the official website:

https://www.python.org/downloads/

**2. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/p2p-file-transfer.git
cd p2p-file-transfer
```

Alternatively, download the repository as a ZIP file and extract it.

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**4. Run the application**

```bash
python p2p_file_transfer.py
```

## Usage

1. Launch the application.
2. Choose the appropriate file transfer action.
3. Follow the instructions displayed in the application.
4. Share the generated transfer code with the other participant when prompted.

Both participants must have the required software and a working network connection.

## Security

This project uses Magic Wormhole for code-based connections and file transfers. Review the underlying dependency's documentation for details about its security model.

Only share transfer codes with intended recipients.

## Compatibility

The application targets Windows 10 and Windows 11. Compatibility depends on the Python version, installed dependencies, and the application's implementation.

Python 3.11 and 3.12 are recommended starting points. Other Python versions should be tested before being considered officially supported.

## License

This project is distributed under the license specified in the `LICENSE` file.

---

**Note:** This project runs directly from its Python source file. No precompiled executable is included.
