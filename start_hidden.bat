@echo off
REM Run URLClipChanger in background without showing a console window
REM This uses the Windows START command with /B flag to start without a new window

REM Check if the application is already compiled as an EXE
if exist ".\dist\URLClipChanger.exe" (
    REM If compiled executable exists, start it
    start /b "" ".\dist\URLClipChanger.exe"
) else (
    REM Otherwise use pythonw.exe (no console window) to run the script
    REM The path to pythonw.exe may need to be adjusted based on your Python installation
    start /b "" pythonw.exe .\src\main.py
)

echo URLClipChanger started in background.
