import argparse
import sys
from pathlib import Path

from src.file_scanner import FileScanner
from src.categorizer import Categorizer
from src.history_manager import HistoryManager
from src.file_mover import FileMover


def parse_args():
    parser = argparse.ArgumentParser(description="Downloads Organizer")
    parser.add_argument(
        "--downloads-path",
        type=Path,
        default=Path.home() / "Downloads",
        help="Path to Downloads folder (default: ~/Downloads)",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path.home() / "Downloads" / "downloads_organized",
        help="Path to organized folder (default: ~/Downloads/downloads_organized)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Server port (default: 5001)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last position",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    downloads_path = Path(args.downloads_path).expanduser()
    output_path = Path(args.output_path).expanduser()
    
    if not downloads_path.exists():
        print(f"Error: Downloads path does not exist: {downloads_path}")
        sys.exit(1)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    scanner = FileScanner()
    categorizer = Categorizer(output_path)
    history_manager = HistoryManager()
    file_mover = FileMover()
    
    print(f"Scanning files in {downloads_path}...")
    files = scanner.scan(downloads_path)
    print(f"Found {len(files)} files")
    
    if args.resume:
        state = history_manager.load_state()
        if state:
            scanner.current_index = state.get("queue_position", 0)
            print(f"Resuming from position {scanner.current_index}")
    
    print(f"Starting server on http://localhost:{args.port}")
    print(f"Open your browser to organize your files")
    print(f"Base output path: {output_path}")
    print(f"Press Ctrl+C to quit")
    
    try:
        from server import create_app, socketio
        app = create_app(
            scanner=scanner,
            categorizer=categorizer,
            history_manager=history_manager,
            file_mover=file_mover,
        )
        socketio.run(app, host="0.0.0.0", port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        
        current, total = scanner.get_progress()
        history_manager.save_state(current, total)
        print(f"State saved: position {current}/{total}")


if __name__ == "__main__":
    main()
