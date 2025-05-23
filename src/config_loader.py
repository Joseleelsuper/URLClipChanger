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
    # Intentamos todas las posibles rutas de configuración
    possible_paths = []
      # Si estamos en un ejecutable PyInstaller
    if getattr(sys, 'frozen', False):
        # 1. Directorio _MEIPASS (directorio temporal de PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            possible_paths.append(Path(getattr(sys, '_MEIPASS')) / "configs")
        
        # 2. Directorio del ejecutable
        exe_dir = Path(os.path.dirname(sys.executable))
        possible_paths.append(exe_dir / "configs")
        
    # 3. Ruta estándar cuando se ejecuta como script
    script_dir = Path(__file__).parent.parent
    possible_paths.append(script_dir / "configs")
    
    # 4. Directorio de trabajo actual
    possible_paths.append(Path(os.getcwd()) / "configs")
    
    # Imprimir información de depuración
    print("Buscando archivos de configuración en:")
    for path in possible_paths:
        print(f"  - {path}")
    
    # Inicializar json_files
    json_files = []
    
    # Buscar en todas las rutas posibles
    for config_path in possible_paths:
        json_files = list(config_path.glob("*.json"))
        if json_files:
            print(f"Encontrados archivos de configuración en: {config_path}")
            break
            
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
