"""
Build script for creating a Windows executable without console window
"""
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    """
    Build the application as a Windows executable with no console window
    """
    print("Building URLClipChanger as a hidden console application...")
    
    # Directory setup
    project_dir = Path(__file__).parent
    build_dir = project_dir / "build"
    dist_dir = project_dir / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Define PyInstaller command
    main_script = project_dir / "src" / "main.py"
    
    # Build arguments
    args = [
        "pyinstaller",
        "--name=URLClipChanger",
        "--noconsole",  # No console window
        "--windowed",   # Windows-specific option for GUI apps
        "--onefile",    # Single executable file
        "--icon=NONE",  # Default icon
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=win32gui",
        "--hidden-import=pyperclip",
        f"--add-data={project_dir / 'configs'};configs",  # Include config folder
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={project_dir}",
        str(main_script)
    ]
    
    try:
        # Run PyInstaller
        subprocess.run(args, check=True)
        
        print(f"\nBuild successful! Executable created at: {dist_dir / 'URLClipChanger.exe'}")
        print("You can now run the application without a visible console window.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())