@echo off
echo Probando endpoint AJAX...
echo.

echo === PROBANDO CON PowerShell ===
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8001/vehiculos-core/api/modelos/?marca_id=1' -Headers @{'Accept'='application/json'} -UseBasicParsing; Write-Host 'Status:' $response.StatusCode; Write-Host 'Content:' $response.Content } catch { Write-Host 'Error:' $_.Exception.Message }"

echo.
echo === FIN PRUEBA ===
pause
