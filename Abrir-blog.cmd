@echo off
setlocal
set "BLOG_DIR=%~dp0"
if not exist "%BLOG_DIR%preview.py" set "BLOG_DIR=%USERPROFILE%\Documents\Blog-chidoliro\"
if not exist "%BLOG_DIR%preview.py" (
  echo No se encuentra la carpeta del blog. Abre este archivo desde Documentos\Blog-chidoliro.
  pause
  exit /b 1
)
cd /d "%BLOG_DIR%"
where python >nul 2>nul
if errorlevel 1 (
  py -3 preview.py
) else (
  python preview.py
)
pause
