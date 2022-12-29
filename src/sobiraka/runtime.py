from pathlib import Path
from typing import Awaitable

class RT:
    TMP: Path | None = None
    AWAITABLES: dict[tuple[callable, tuple, tuple], Awaitable] = {}
