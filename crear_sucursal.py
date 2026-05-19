import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventario.models import Sucursal

# Crear sucursal
sucursal, created = Sucursal.objects.get_or_create(
    nombre='Tiendita del Chino',
    defaults={
        'ubicacion': 'Centro Local'
    }
)

if created:
    print(f'✓ Sucursal creada: {sucursal.nombre}')
    print(f'  Ubicación: {sucursal.ubicacion}')
    print(f'  ID: {sucursal.id}')
else:
    print(f'✓ Sucursal ya existe: {sucursal.nombre}')
    print(f'  Ubicación: {sucursal.ubicacion}')
    print(f'  ID: {sucursal.id}')

print('\n' + '='*50)
print('SUCURSAL LISTA')
print('='*50)
