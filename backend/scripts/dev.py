from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent


def main() -> int:
    run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND_DIR)
    run([sys.executable, "scripts/seed.py"], cwd=BACKEND_DIR)

    processes = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND_DIR,
        ),
        subprocess.Popen(["npm", "--prefix", str(REPO_DIR / "frontend"), "run", "dev"], cwd=REPO_DIR),
    ]

    stopping = False

    def stop(_: int | None = None, __: object | None = None) -> None:
        nonlocal stopping
        stopping = True
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    stop()
                    return 0 if stopping else code
            time.sleep(0.5)
    finally:
        stop()


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
