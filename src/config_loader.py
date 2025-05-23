import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

Rule = Tuple[List[str], str]


def load_rules() -> List[Rule]:
    """Load rules from a JSON file.

    Raises:
        FileNotFoundError: If no rules JSON file is found.

    Returns:
        List[Rule]: A list of rules, where each rule is a tuple containing:
                    a list of domains and a suffix to add.
    """
    # Primero intentamos la ruta estándar cuando se ejecuta como script
    config_path = Path(__file__).parent.parent / "configs"
    
    # Si estamos en un ejecutable PyInstaller
    if getattr(sys, 'frozen', False):
        # PyInstaller crea un directorio temporal y guarda la ruta en _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        config_path = Path(base_path) / "configs"
    
    json_files = list(config_path.glob("*.json"))
    if not json_files:
        # Buscar en rutas alternativas
        alt_paths = [
            Path.cwd() / "configs",
            Path(sys.executable).parent / "configs"
        ]
        
        for path in alt_paths:
            json_files = list(path.glob("*.json"))
            if json_files:
                break
                
    if not json_files:
        raise FileNotFoundError("No rules JSON file found in any of the searched paths.")
        
    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    return [(r["domains"], r["suffix"]) for r in data]
