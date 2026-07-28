@echo off
set /p DBNAME="Enter Database Name: "
echo Launching Odoo Shell for %DBNAME%...
D:\Odoo\venv\Scripts\python.exe D:\Odoo\odoo\odoo-bin shell -c D:\odoo-mcp\odoo.conf -d %DBNAME%
pause
