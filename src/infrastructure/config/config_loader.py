import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import appdirs

current_dir = os.path.dirname(os.path.abspath(__file__))

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
    app_name = "URLClipChanger"

    # If running in a PyInstaller bundle
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent / "configs"
        paths.append(exe_dir / "rules.json")
    # 2. User config directory
    try:
        user_config_dir = Path(appdirs.user_config_dir(app_name))
        paths.append(user_config_dir / "rules.json")
    except ImportError:
        pass

    # 3. Project directory
    project_dir = Path(__file__).resolve().parent.parent.parent.parent / "configs"
    paths.append(project_dir / "rules.json")

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
