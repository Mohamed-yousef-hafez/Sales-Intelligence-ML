@echo off
REM Refreshes the Power BI files once. Use it with Windows Task Scheduler (for example every hour).
REM Put the new sales file in the "inbox" folder first. Add --combine to use all files in the folder.
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python refresh_exports.py %*
