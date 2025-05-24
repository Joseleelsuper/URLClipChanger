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
    
    # Determine which mode to build
    build_mode = "cli"
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["gui", "cli", "both"]:
        build_mode = sys.argv[1].lower()
    
    # Common PyInstaller arguments
    common_args = [
        "--noconsole",  # No console window
        "--windowed",   # Windows-specific option for GUI apps
        "--onefile",    # Single executable file
        f"--icon={project_dir / 'icon' / 'URLClipChanger.ico'}",  # Use custom icon
        # Fix module imports for PyInstaller
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "--hidden-import=win32gui",
        "--hidden-import=win32clipboard",
        "--hidden-import=pyperclip",
        "--hidden-import=tkinter",
        "--hidden-import=appdirs",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageTk",
        "--hidden-import=pystray",
        "--hidden-import=uuid",
        "--hidden-import=winshell",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=win32ui",
        "--paths=src",
        # Clean the temporary files when the application exits
        "--clean",
        f"--add-data={project_dir / 'configs'};configs",  # Include config folder
        f"--add-data={project_dir / 'icon'};icon",  # Include icon folder
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={project_dir}",
    ]
    
    builds_to_run = []
    
    if build_mode in ["cli", "both"]:
        # CLI version (background service)
        cli_script = project_dir / "src" / "app" / "main.py"
        cli_args = ["pyinstaller", "--name=URLClipChanger"] + common_args + [str(cli_script)]
        builds_to_run.append(("CLI", cli_args))
    
    if build_mode in ["gui", "both"]:
        # GUI version
        gui_script = project_dir / "src" / "app" / "gui_main.py"
        gui_args = ["pyinstaller", "--name=URLClipChangerGUI"] + common_args + [str(gui_script)]
        builds_to_run.append(("GUI", gui_args))
    
    success = True
    
    for build_type, args in builds_to_run:
        try:
            print(f"\nRunning PyInstaller for {build_type} version...")
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            
            # Print PyInstaller output for debugging
            if result.stdout:
                print(f"\nPyInstaller {build_type} Output:")
                print(result.stdout)
            
            if result.stderr:
                print(f"\nPyInstaller {build_type} Errors/Warnings:")
                print(result.stderr)
                
            print(f"{build_type} build successful!")
            
        except subprocess.CalledProcessError as e:
            print(f"{build_type} build failed with exit code {e.returncode}")
            if e.stdout:
                print(f"\n{build_type} Output:")
                print(e.stdout)
            if e.stderr:
                print(f"\n{build_type} Error output:")
                print(e.stderr)
            success = False
    
    if success:
        # Copy additional required files
        copy_required_files(dist_dir, project_dir)
        
        print("\nAll builds completed successfully!")
        if build_mode == "both":
            print(f"Executables created at: \n - {dist_dir / 'URLClipChanger.exe'} (background service)\n - {dist_dir / 'URLClipChangerGUI.exe'} (GUI application)")
        elif build_mode == "gui":
            print(f"Executable created at: {dist_dir / 'URLClipChangerGUI.exe'}")
        else:
            print(f"Executable created at: {dist_dir / 'URLClipChanger.exe'}")
        return 0
    else:
        print("\nOne or more builds failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())