import subprocess
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir / "backend"
    frontend_dir = base_dir / "frontend"

    # Start backend (uvicorn or `uv run main.py`)
    print("🚀 Starting backend...")
    backend_process = subprocess.Popen(
        ["uv run main.py"],
        cwd=backend_dir,
        shell=True
    )

    # Start frontend (npm start)
    print("🚀 Starting frontend...")
    frontend_process = subprocess.Popen(
        ["npm start"],
        cwd=frontend_dir,
        shell=True
    )

    try:
        # Wait for both to finish (usually they run indefinitely)
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down both processes...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
