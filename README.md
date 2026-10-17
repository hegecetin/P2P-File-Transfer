📁 Easy File Transfer

A simple Windows desktop application for transferring files and folders between computers, built with Python and Tkinter.

The application provides a graphical interface for sending and receiving files without complicated terminal commands. It uses Magic Wormhole for file transfers.

✨ Features

Send Files: Send selected files to another computer.

Send Folders: Transfer folders easily.

Receive Files and Folders: Save incoming content to a selected location.

Transfer Codes: Connect the sender and recipient using a generated transfer code.

Copy Codes: Copy transfer codes to the clipboard.

Transfer Progress: Monitor transfer status, progress, and speed when available.

Language Support: Turkish and English interface.

Settings: Manage application preferences.

Activity Log: Review transfer operations in versions that include logging.

🖥️ Requirements

Windows 10 or Windows 11

Python 3

Internet connection

Magic Wormhole

🚀 Installation

1. Clone the Repository

git clone https://github.com/YOUR_USERNAME/REPOSITORY_NAME.git
cd REPOSITORY_NAME

Replace YOUR_USERNAME and REPOSITORY_NAME with your GitHub username and repository name.

2. Install Dependencies

python -m pip install --upgrade "magic-wormhole>=0.23.0"

3. Run the Application

python main.py

Replace main.py with your actual Python filename if necessary.

📤 How to Use

Open the application on the sender's computer.

Go to the Send File tab.

Select the file or folder you want to transfer.

Start the transfer and share the generated code with the recipient.

Open the application on the recipient's computer.

Go to the Receive File tab.

Enter the transfer code and choose a destination folder.

Wait for the transfer to complete.

Note: The computers do not need to be connected to the same local network. Both computers need internet access, and connectivity may depend on network and firewall settings.

🔐 Security and Privacy

Uses the security mechanisms provided by Magic Wormhole.

Share transfer codes only with the intended recipient.

Do not share transfer codes publicly.

Do not accept transfer codes from untrusted sources.

Development note: Six-digit numeric PIN pairing, Supabase-based matchmaking, and direct WebRTC transfers are not available unless they have been implemented and tested.

🧾 Activity Log

Versions that include activity logging can record transfer operations and their results locally.

Logs can help with troubleshooting and reviewing previous operations. Check log contents before sharing them, as they may contain sensitive information.

🛠️ Technologies Used

Python — Application logic

Tkinter / ttk — Graphical user interface

Magic Wormhole — File transfer infrastructure

JSON — Application settings and log data

🗺️ Roadmap

Six-digit numeric PIN pairing

Improved connectivity across different networks

Secure session management and rate limiting

Supabase-based matchmaking

Windows executable (.exe) release

🤝 Contributing

Suggestions, bug reports, and contributions are welcome. Feel free to open an issue or submit a pull request.

