# ACC Server Companion

A web-based tool to manage [Assetto Corsa Competizione](https://www.assettocorsa.it/competizione/) (ACC) dedicated servers.

## Objective

This tool simplifies the editing of the server's JSON configuration files, eliminating syntax errors and making it easy to create custom events.

## Features

- Visual editor for the following files:
  - `configuration.json` (network)
  - `settings.json` (identification and requirements)
  - `event.json` (track, weather, sessions)
  - `eventRules.json` (sporting rules)
  - `entrylist.json`, `assistRules.json`, `bop.json` (advanced)
- Track selector with images and automatic pitbox limits.
- Real-time validation (UDP/TCP ports, SteamID, grid limits).
- Presets: save and load complete server configurations.
- Start the server directly from the interface.
- Create a desktop shortcut (`.bat`).
- Dark theme with neon colors.

## Technologies Used

- **Backend:** Python with [Flask](https://flask.palletsprojects.com/)
- **Frontend:** [Alpine.js](https://alpinejs.dev/) for reactive components
- **UI:** Custom CSS for a dark theme

## Installation

### Prerequisites

- [Python 3](https://www.python.org/downloads/)
- [ACC Dedicated Server](https://steamcommunity.com/app/247800/discussions/0/1697168437877299041/) installed via Steam

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/acc-server-companion.git
    cd acc-server-companion/acc-server-tool
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will open in your web browser at `http://localhost:5000`.

2.  **Set the server directory:**
    - On the "Initial Setup" tab, click "Change Server Folder" and select the root directory of your ACC Dedicated Server (the one containing `accServer.exe`).

3.  **Configure your server:**
    - Navigate through the tabs to edit the different configuration files.
    - Your changes are saved automatically when you click the "Save" button on each page.

4.  **Start the server:**
    - Click the "START SERVER" button to launch the `accServer.exe` process.

## Contributing

Contributions are welcome! If you have ideas for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
