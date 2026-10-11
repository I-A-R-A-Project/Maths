import subprocess
import sys


def main() -> int:
    command = [sys.executable, "-m", "pytest", "tests"]
    print("Running:", " ".join(command))
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
