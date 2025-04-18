@echo off
echo Cleaning up unnecessary files and directories...

rmdir /s /q fresh_env
rmdir /s /q new_env
rmdir /s /q venv_new
rmdir /s /q fresh_venv
rmdir /s /q new_venv
rmdir /s /q .venv
rmdir /s /q env
rmdir /s /q audius

del /q .cache

echo Cleanup complete!
pause 