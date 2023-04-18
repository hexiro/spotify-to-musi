from __future__ import annotations

import pathlib
import sys

import rich.traceback

rich.traceback.install()

sys.path.append(str(pathlib.Path(__file__).parent))
