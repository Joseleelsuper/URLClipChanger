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
    """Determines a prioritized list of absolute paths to check for rules.json
    The order of paths reflects the priority for searching.

    Returns:
        List[Path]: A list of Paths to potential rules.json files in order of priority.
    """
    paths: List[Path] = []
    app_name = "URLClipChanger"

    # 1. If running in a PyInstaller bundle
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

    # Remove duplicates while preserving order
    unique_paths = []
    for p in paths:
        if p not in unique_paths:
            unique_paths.append(p)
    
    return unique_paths


def _find_config_file_in_paths(config_search_paths: List[Path]) -> Optional[Path]:
    """Searches for the rules.json file in the given list of paths.
    
    Args:
        config_search_paths (List[Path]): A list of paths to check for rules.json.

    Returns:
        Optional[Path]: The Path to the found configuration file, or None if not found.
    """
    logger.info(
        "Searching for configuration files in the following prioritized paths:"
    )
    for path in config_search_paths:
        logger.debug(f"  - Checking: {path}")

        # If path is a file, check if it exists directly
        if path.is_file():
            logger.info(f"  -> Found configuration file: {path}")
            return path
        
        # If path is a directory, check for rules.json inside
        elif path.is_dir():
            rules_file = path / "rules.json"
            if rules_file.is_file():
                logger.info(f"  -> Found configuration file: {rules_file}")
                return rules_file
        
        # Check if parent directory exists
        elif path.parent.is_dir():
            logger.debug(f"  - File not found: {path}")
        else:
            logger.debug(f"  - Parent directory not found: {path.parent}")
            
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

    # Create default rules file if not found
    if not config_file_path:
        # Try to create and save a default sample rules file
        try:
            # Use the first path from the search paths as the default location
            default_path = search_paths[0]
            
            # Create parent directories if they don't exist
            if not default_path.parent.exists():
                default_path.parent.mkdir(parents=True, exist_ok=True)
                
            # Create default rules file with example content
            default_rules = [
                {
                    "domains": [
                        "example.com",
                        "example.es"
                    ],
                    "suffix": "?ref=URLClipChanger"
                }
            ]
            
            # Write the default rules
            with open(default_path, "w", encoding="utf-8") as f:
                json.dump(default_rules, f, indent=4)
                
            logger.info(f"Created default rules file with example content at: {default_path}")
            config_file_path = default_path
        except Exception as e:
            logger.error(f"Failed to create default rules file: {e}")
            searched_paths_str = "\n".join([f"  - {p}" for p in search_paths])
            raise FileNotFoundError(
                "No rules JSON file found. Searched in the following paths:\n"
                f"{searched_paths_str}"
            )

    logger.info(f"Loading rules from: {config_file_path}")
    with open(config_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [(r["domains"], r["suffix"]) for r in data]
