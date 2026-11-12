import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
APP = ROOT / "app"

# Make repo root importable so `app.rag.*` resolves
sys.path.insert(0, str(ROOT))
# Make `app/` importable so bare `rag.clients.*` (used by index.py) resolves
sys.path.insert(0, str(APP))

import os
from dotenv import load_dotenv
load_dotenv()
