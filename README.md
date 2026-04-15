# File Sorter

A web-based Python application that interactively organizes files from a Downloads folder into a structured directory. Uses Flask with WebSocket for real-time updates and an HTML5 frontend.

## Features

- Interactive file organization through a web interface
- Real-time progress tracking with WebSocket
- Resume from last position after restart
- Customizable source and destination paths
- Keyboard shortcuts for fast file sorting

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Start the server (default port 5001 to avoid AirPlay conflict)
python organizer.py

# With custom options
python organizer.py --downloads-path ~/Downloads --output-path ~/Downloads/downloads_organized --port 5001

# Resume from last position
python organizer.py --resume
```

Then open your browser to `http://localhost:5001` to start organizing files.

## Dependencies

- Flask >= 2.0.0
- Flask-SocketIO >= 5.0.0
- python-socketIO >= 5.0.0
- eventlet >= 0.30.0

## Project Structure

```
file_sorter/
├── organizer.py          # Entry point
├── server.py             # Flask app and API endpoints
├── requirements.txt      # Python dependencies
├── src/
│   ├── file_scanner.py   # Scans filesystem
│   ├── categorizer.py    # Provides folder categorization
│   ├── history_manager.py # Tracks progress
│   └── file_mover.py     # Handles file movement
└── static/               # Frontend assets
```