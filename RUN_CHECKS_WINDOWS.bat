@echo off
setlocal
cd /d "%~dp0"
echo ======================================================
echo HHO-GWO project checks
echo Project folder: %CD%
echo ======================================================
py -m pip install -r requirements.txt
if errorlevel 1 goto fail
py -m unittest discover -s tests -v
if errorlevel 1 goto fail
py experiments\run_smoke_test.py
if errorlevel 1 goto fail
echo.
echo SUCCESS: dependency install, unit tests and smoke test completed.
echo Save this terminal output as part of your validation record.
pause
exit /b 0
:fail
echo.
echo FAILED: read the error above and share the complete terminal output.
pause
exit /b 1
