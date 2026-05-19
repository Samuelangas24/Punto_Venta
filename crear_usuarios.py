import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Crear usuario administrador
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@puntoventa.local',
        'is_staff': True,
        'is_superuser': True,
        'is_active': True
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print('✓ Usuario Administrador creado: admin / admin123')
else:
    admin_user.set_password('admin123')
    admin_user.save()
    print('✓ Usuario Administrador actualizado: admin / admin123')

# Crear usuario trabajador/normal
worker_user, created = User.objects.get_or_create(
    username='trabajador',
    defaults={
        'email': 'trabajador@puntoventa.local',
        'is_staff': False,
        'is_superuser': False,
        'is_active': True
    }
)
if created:
    worker_user.set_password('trabajador123')
    worker_user.save()
    print('✓ Usuario Trabajador creado: trabajador / trabajador123')
else:
    worker_user.set_password('trabajador123')
    worker_user.save()
    print('✓ Usuario Trabajador actualizado: trabajador / trabajador123')

print('\n' + '='*50)
print('CREDENCIALES CREADAS EXITOSAMENTE')
print('='*50)
print('\n👤 ADMINISTRADOR:')
print('   Usuario: admin')
print('   Contraseña: admin123')
print('   Acceso: Panel Administrativo + Todas las funciones')
print('\n👤 TRABAJADOR:')
print('   Usuario: trabajador')
print('   Contraseña: trabajador123')
print('   Acceso: Solo funciones de punto de venta')
print('\n' + '='*50)
