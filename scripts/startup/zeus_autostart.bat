@echo off
rem AI4OHS-HYBRID - Zeus Prompt Listener Autostart
set REPO_DIR=%~dp0..\..
pushd %REPO_DIR%
python scripts\dev\zeus_prompt_listener.py
popd
