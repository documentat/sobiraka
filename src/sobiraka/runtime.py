from importlib.abc import Traversable
from importlib.resources import files
from pathlib import Path
from typing import Awaitable

class RT:
    FILES: Traversable = files('sobiraka') / 'files'
    TMP: Path | None = None
    AWAITABLES: dict[tuple[callable, tuple, tuple], Awaitable] = {}
