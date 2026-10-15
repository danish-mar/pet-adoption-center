#!/usr/bin/env python3
"""Runner for PawHaven WebUI server."""

import os
import sys
from pathlib import Path

# Automatically switch to project virtualenv if running outside it
root_dir = Path(__file__).resolve().parent
venv_python = root_dir / ".venv" / "bin" / "python"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

# Ensure src is on sys.path
src_path = root_dir / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from pet_adoption_center.web.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🐾 Starting PawHaven WebUI on http://localhost:{port} ...")
    app.run(host="0.0.0.0", port=port, debug=True)
