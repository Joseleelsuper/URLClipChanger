"""
Build script for creating a Windows executable without console window
"""
import sys
import shutil
import subprocess
from pathlib import Path


def cleanup_old_builds(build_dir, dist_dir):
    """Clean up previous builds"""
    print("Cleaning up previous builds...")
    
    if build_dir.exists():
        try:
            shutil.rmtree(build_dir)
            print("Build directory cleaned.")
        except Exception as e:
            print(f"Warning: Could not clean build directory: {e}")
            
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir)
            print("Dist directory cleaned.")
        except Exception as e:
            print(f"Warning: Could not clean dist directory: {e}")


def copy_required_files(dist_dir, project_dir):
    """Copy necessary files to the distribution folder"""
    print("Copying required files to distribution directory...")
    
    try:
        # Create logs directory if it doesn't exist
        logs_dir = dist_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        print("Created logs directory.")
        
        # Copy configs folder
        config_src = project_dir / "configs"
        config_dest = dist_dir / "configs"
        if config_src.exists():
            if config_dest.exists():
                shutil.rmtree(config_dest)
            shutil.copytree(config_src, config_dest)
            print("Copied configs directory.")
    except Exception as e:
        print(f"Warning: Error copying files: {e}")


def main():
    """
    Build the application as a Windows executable without console window
    """
    print("Building URLClipChanger as a hidden console application...")
    
    # Directory setup
    project_dir = Path(__file__).parent
    build_dir = project_dir / "build"
    dist_dir = project_dir / "dist"
      # Clean previous builds
    cleanup_old_builds(build_dir, dist_dir)
    
    # Define PyInstaller command
    main_script = project_dir / "src" / "app" / "main.py"
    args = [
        "pyinstaller",
        "--name=URLClipChanger",
        "--noconsole",  # No console window
        "--windowed",   # Windows-specific option for GUI apps
        "--onefile",    # Single executable file
        f"--icon={project_dir / 'icon' / 'URLClipChanger.ico'}",  # Use custom icon
        # Fix module imports for PyInstaller
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=win32gui",
        "--hidden-import=win32clipboard",
        "--hidden-import=pyperclip",        # Important: Add src to path to fix imports
        "--paths=src",
        # Clean the temporary files when the application exits
        "--clean",
        f"--add-data={project_dir / 'configs'};configs",  # Include config folder
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={project_dir}",
        str(main_script)
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        
        # Print PyInstaller output for debugging
        if result.stdout:
            print("\nPyInstaller Output:")
            print(result.stdout)
        
        if result.stderr:
            print("\nPyInstaller Errors/Warnings:")
            print(result.stderr)
            
        # Copy additional required files
        copy_required_files(dist_dir, project_dir)
        
        print(f"\nBuild successful! Executable created at: {dist_dir / 'URLClipChanger.exe'}")
        print("You can now run the application without a visible console window.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        if e.stdout:
            print("\nOutput:")
            print(e.stdout)
        if e.stderr:
            print("\nError output:")
            print(e.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())