from importlib.resources import files
from pathlib import Path
from typing import Awaitable

class RT:
    FILES: Path = files('sobiraka') / 'files'
    TMP: Path | None = None
    AWAITABLES: dict[tuple[callable, tuple, tuple], Awaitable] = {}
    IDS: dict[int, str] = {}
