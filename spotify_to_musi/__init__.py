from __future__ import annotations

import pathlib
import sys

import dotenv

dotenv.load_dotenv()
sys.path.append(str(pathlib.Path(__file__).parent))
