@echo off
REM Local test gate for daily-order-report. ASCII only (cmd cp949 safe).
chcp 65001 >nul
cd /d %~dp0
echo === daily-order-report test gate ===
python -X utf8 -m unittest discover -s tests -t . -p "test_*.py" -v
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo RESULT: TESTS FAILED
  exit /b 1
)
echo.
echo RESULT: ALL TESTS PASSED
