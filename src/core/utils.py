import json
from pathlib import Path
from typing import Any


def load_json_file(path: str | Path) -> Any:
    """ Load and parse a JSON file. """
    file_path = Path(path)

    # r stands for read mode.
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
