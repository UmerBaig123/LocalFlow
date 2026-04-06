"""Entry point: python -m localflow"""

import os
import sys
from pathlib import Path

# Add bundled lib/ to LD_LIBRARY_PATH so sounddevice can find portaudio.
# LD_LIBRARY_PATH must be set before the process loads shared libs, so if
# it wasn't set we re-exec ourselves with the updated environment.
_lib_dir = str(Path(__file__).resolve().parent.parent / "lib")
if os.path.isdir(_lib_dir):
    current = os.environ.get("LD_LIBRARY_PATH", "")
    if _lib_dir not in current:
        os.environ["LD_LIBRARY_PATH"] = _lib_dir + (":" + current if current else "")
        os.execv(sys.executable, [sys.executable] + sys.argv)

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")


def main():
    from localflow.app import run
    sys.exit(run())


if __name__ == "__main__":
    main()
