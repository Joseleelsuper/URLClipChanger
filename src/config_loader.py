import json
from pathlib import Path
from typing import List, Tuple

Rule = Tuple[List[str], str]


def load_rules() -> List[Rule]:
    config_path = Path(__file__).parent.parent / "configs"
    json_files = list(config_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError("No rules JSON file found.")
    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    return [(r["domains"], r["suffix"]) for r in data]
