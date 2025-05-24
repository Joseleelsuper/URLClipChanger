import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))
# instead of pointing to the app folder, point to src so `import shared…` works
src_path = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, src_path)

from infrastructure.logging.logger import logger  # noqa: E402

Rule = Tuple[List[str], str]


def _get_prioritized_config_paths() -> List[Path]:
    """Determines a prioritized list of absolute paths to 'configs' directories
    where configuration files might be located.
    The order of paths reflects the priority for searching.

    Returns:
        List[Path]: A list of Paths to 'configs' directories in order of priority.
    """
    paths: List[Path] = []

    # If running in a PyInstaller bundle
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            paths.append(Path(getattr(sys, "_MEIPASS")).resolve() / "configs")
        exe_dir = Path(os.path.dirname(sys.executable)).resolve()
        paths.append(exe_dir / "configs")
    else:
        script_project_root = Path(__file__).resolve().parent.parent
        paths.append(script_project_root / "configs")
    paths.append(Path(os.getcwd()).resolve() / "configs")

    unique_paths: List[Path] = []
    for p in paths:
        if p not in unique_paths:
            unique_paths.append(p)

    return unique_paths


def _find_config_file_in_paths(config_search_paths: List[Path]) -> Optional[Path]:
    """Searches for the first '*.json' file in the given list of 'configs' directories.
    Returns the Path to the file if found, otherwise None.

    Args:
        config_search_paths (List[Path]): A list of Paths to 'configs' directories to search.

    Returns:
        Optional[Path]: The Path to the found configuration file, or None if not found.
    """
    logger.info(
        "Searching for configuration files in the following prioritized 'configs' directories:"
    )
    for config_dir_path in config_search_paths:
        logger.debug(f"  - Checking: {config_dir_path}")
        if config_dir_path.is_dir():
            json_files = sorted(list(config_dir_path.glob("*.json")))
            if json_files:
                found_file = json_files[0]
                logger.info(f"  -> Found configuration file: {found_file}")
                return found_file
        else:
            logger.debug(f"  - Directory not found: {config_dir_path}")
    logger.warning("No configuration file found in any of the searched paths.")
    return None


def load_rules() -> List[Rule]:
    """Load rules from a JSON file.

    Raises:
        FileNotFoundError: If no rules JSON file is found in any of the
                           standard locations.

    Returns:
        List[Rule]: A list of rules, where each rule is a tuple containing:
                    a list of domains and a suffix to add.
    """
    search_paths = _get_prioritized_config_paths()

    config_file_path = _find_config_file_in_paths(search_paths)

    if not config_file_path:
        searched_paths_str = "\\n".join([f"  - {p}" for p in search_paths])
        logger.error("No rules JSON file found.")
        raise FileNotFoundError(
            "No rules JSON file found. Searched in the following 'configs' directories:\n"
            f"{searched_paths_str}"
        )

    logger.info(f"Loading rules from: {config_file_path}")
    with open(config_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [(r["domains"], r["suffix"]) for r in data]
