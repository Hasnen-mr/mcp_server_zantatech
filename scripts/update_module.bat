@echo off
set /p DBNAME="Enter Database Name: "
echo Updating mcp_connector on database %DBNAME%...
D:\Odoo\venv\Scripts\python.exe D:\Odoo\odoo\odoo-bin -c D:\odoo-mcp\odoo.conf -u mcp_connector -d %DBNAME%
pause
