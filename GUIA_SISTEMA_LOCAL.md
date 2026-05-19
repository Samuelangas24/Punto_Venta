# 🛒 Sistema Punto de Venta - Guía de Uso Local

## Configuración Completada ✅

El sistema ha sido migrado de SQLite a **MySQL** y está configurado para funcionar **sin conexión a internet**.

### Configuración Actual

**Base de Datos:**
- Motor: MySQL
- Host: `localhost`
- Puerto: `3305`
- Usuario: `root`
- Contraseña: `12345`
- Base de datos: `punto_de_venta`

**Servidor Web:**
- Dirección: `http://127.0.0.1:8000/`
- Modo: Aplicación local (sin internet)
- Acceso: Solo desde este equipo

---

## 📋 Requisitos del Sistema

1. **MySQL** corriendo en puerto `3305`
2. **Python 3.12+** con entorno virtual activado
3. **Windows PowerShell** para ejecutar scripts

---

## 🚀 Cómo Iniciar el Sistema

### Opción 1: Script Automático (Recomendado)

1. Abre PowerShell en la carpeta del proyecto
2. Ejecuta:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   .\iniciar_sistema.ps1
   ```
3. Espera el mensaje: `El sistema estará disponible en: http://127.0.0.1:8000/`

### Opción 2: Manual

1. Abre PowerShell en la carpeta del proyecto
2. Activa el entorno virtual:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Inicia el servidor:
   ```powershell
   python manage.py runserver 127.0.0.1:8000
   ```

---

## 🌐 Acceso a la Aplicación

Una vez iniciado, accede desde el navegador:

- **Página de Inicio:** `http://127.0.0.1:8000/`
- **Iniciar Sesión:** `http://127.0.0.1:8000/login/`

---

## 👤 Credenciales Predeterminadas

Para crear un usuario administrativo, ejecuta:

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Crear superusuario (el sistema pedirá datos)
python manage.py createsuperuser
```

---

## 📦 Características del Sistema

✅ Funciona completamente sin internet  
✅ Base de datos MySQL local  
✅ Sin dependencias de CDN  
✅ Interfaz intuitiva y responsiva  
✅ Gestión de inventario  
✅ Sistema de ventas  
✅ Reportes y corte de caja  

---

## 🔧 Comandos Útiles de Django

```powershell
# Crear migraciones (si modificas modelos)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Acceder a la consola interactiva Django
python manage.py shell

# Recolectar archivos estáticos
python manage.py collectstatic

# Ver estado de la base de datos
python manage.py dbshell
```

---

## 🛑 Detener el Sistema

Presiona `Ctrl + C` en PowerShell mientras el servidor está corriendo.

---

## 📝 Notas Importantes

- **No requiere internet**: La aplicación funciona completamente offline
- **Almacenamiento local**: Todos los datos se guardan en MySQL local
- **Seguridad**: Por defecto solo accesible desde `127.0.0.1`
- **Base de datos**: Se conecta automáticamente a MySQL en puerto 3305

---

## ⚠️ Solución de Problemas

### Error: "Can't connect to MySQL"
- Verifica que MySQL esté corriendo en puerto 3305
- Comprueba que el usuario `root` con contraseña `12345` exista en MySQL

### Error: "Unknown database 'punto_de_venta'"
- Ejecuta nuevamente el script de inicialización:
  ```powershell
  python manage.py migrate
  ```

### Puerto 8000 en uso
- Cambia a otro puerto en `iniciar_sistema.ps1`:
  ```powershell
  python manage.py runserver 127.0.0.1:8001
  ```

---

## 📞 Soporte

Para más información sobre Django, visita: https://www.djangoproject.com/

*(Esta documentación es para uso local. No requiere conexión a internet después del setup inicial)*
