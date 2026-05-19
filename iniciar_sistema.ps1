# Script para iniciar el Sistema Punto de Venta - Sin Internet
# Este script inicia Django en localhost:8000 sin dependencias externas

Write-Host "================================" -ForegroundColor Green
Write-Host "Sistema Punto de Venta - Local" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Activar el entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Verificar conexión a MySQL
Write-Host "Verificando conexión a MySQL..." -ForegroundColor Yellow
try {
    & ".venv\Scripts\python.exe" -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345',
        port=3305,
        database='punto_de_venta'
    )
    conn.close()
    print('✓ Conexión a MySQL exitosa')
except Exception as e:
    print(f'✗ Error de conexión: {e}')
    exit(1)
"
} catch {
    Write-Host "Error: No se pudo conectar a MySQL. Verifica que MySQL esté corriendo en puerto 3305" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Iniciando servidor Django..." -ForegroundColor Yellow
Write-Host "El sistema estará disponible en: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Cyan
Write-Host ""

# Iniciar servidor Django
& ".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

Write-Host ""
Write-Host "Servidor detenido" -ForegroundColor Yellow
