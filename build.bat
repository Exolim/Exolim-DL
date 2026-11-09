@echo off
REM Сборка Exolim-DL.exe (onefile, с консолью)
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --name Exolim-DL ^
  --collect-all imageio_ffmpeg ^
  --distpath releases ^
  --workpath build ^
  --specpath build ^
  src\exolim.py
echo.
echo Готово: releases\Exolim-DL.exe
pause
