import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Command failed: {command}", file=sys.stderr)
        sys.exit(result.returncode)

def setup_frontend(base_dir):
    frontend_dir = base_dir / "frontend"
    if not frontend_dir.exists():
        print("Frontend directory not found. Skipping frontend setup.", file=sys.stderr)
        return

    print("\n🔧 Setting up frontend...")
    run_command("npm install", cwd=frontend_dir)
    print("✅ Frontend setup complete.")

def main():
    base_dir = Path(__file__).resolve().parent
    setup_frontend(base_dir)

if __name__ == "__main__":
    main()
