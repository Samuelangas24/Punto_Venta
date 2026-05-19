from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Sum, Q
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from .models import Venta, DetalleVenta, CorteCaja
from inventario.models import Sucursal, Producto, InventarioSucursal, Seccion
from usuarios.decoradores import rol_requerido, solo_activos
from decimal import Decimal, InvalidOperation
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO

@login_required(login_url='login')
@rol_requerido('admin', 'cajero')
@solo_activos
def reporte_ventas(request):
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')
    sucursal_id = request.session.get('sucursal_id')

    # Filtramos las ventas
    ventas = Venta.objects.all()
    
    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date__range=[fecha_inicio_date, fecha_fin_date])
        except ValueError:
            pass
    
    if sucursal_id:
        ventas = ventas.filter(sucursal_id=sucursal_id)

    total_generado = ventas.aggregate(Sum('total'))['total__sum'] or 0

    return render(request, 'admin/reporte.html', {
        'ventas': ventas,
        'total_generado': total_generado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def api_estadisticas_hoy(request):
    """API para obtener estadísticas del día actual"""
    from datetime import date
    sucursal_id = request.session.get('sucursal_id')
    
    hoy = date.today()
    ventas_hoy = Venta.objects.filter(
        sucursal_id=sucursal_id,
        fecha__date=hoy
    )
    
    total_ventas = ventas_hoy.count()
    total_ingresos = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    
    # Contar productos únicos vendidos hoy
    productos_vendidos = DetalleVenta.objects.filter(
        venta__in=ventas_hoy
    ).values('producto').distinct().count()
    
    return JsonResponse({
        'total_ventas': total_ventas,
        'total_ingresos': float(total_ingresos),
        'productos_vendidos': productos_vendidos
    })


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def buscar_producto(request):
    """API para buscar productos por código de barras o descripción"""
    query = request.GET.get('q', '').strip()
    sucursal_id = request.session.get('sucursal_id')
    
    if not query:
        return JsonResponse({'productos': []})

    # Buscar primero por código de barras exacto para el lector
    productos = Producto.objects.filter(
        codigo_barras__iexact=query
    )

    if not productos.exists():
        if len(query) < 2:
            return JsonResponse({'productos': []})

        productos = Producto.objects.filter(
            Q(codigo_barras__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )[:20]
    
    resultado = []
    for producto in productos:
        # Obtener stock disponible
        try:
            inventario = InventarioSucursal.objects.get(
                sucursal_id=sucursal_id,
                producto=producto
            )
            stock = inventario.cantidad
        except InventarioSucursal.DoesNotExist:
            stock = 0
        
        resultado.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'codigo_barras': producto.codigo_barras or 'Sin código',
            'precio': float(producto.precio_venta),
            'stock': stock,
            'descripcion': producto.descripcion or ''
        })
    
    return JsonResponse({'productos': resultado})


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero')
@solo_activos
def crear_venta_page(request):
    """Página interactiva de punto de venta.

    El sistema está diseñado para ser multifuncional: hasta 9 usuarios
    pueden operar simultáneamente en diferentes sucursales. El administrador
    tiene acceso global para gestionar inventarios y sucursales desde el panel."""
    sucursal_id = request.session.get('sucursal_id')
    sucursal_nombre = request.session.get('sucursal_nombre')
    
    return render(request, 'crear_venta.html', {
        'sucursal': sucursal_nombre,
        'usuario': request.user.username,
    })


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def almacen_admin(request):
    """Administración de productos y sucursales desde el almacén."""
    sucursales = Sucursal.objects.all().order_by('nombre')
    secciones = Seccion.objects.all().order_by('nombre')
    sucursal_id = request.GET.get('sucursal')
    sucursal_seleccionada = None
    inventario = []

    if sucursal_id:
        sucursal_seleccionada = Sucursal.objects.filter(id=sucursal_id).first()
        if sucursal_seleccionada:
            inventario = InventarioSucursal.objects.filter(
                sucursal=sucursal_seleccionada
            ).select_related('producto').order_by('producto__nombre')

    return render(request, 'admin/almacen.html', {
        'sucursales': sucursales,
        'secciones': secciones,
        'sucursal_seleccionada': sucursal_seleccionada,
        'inventario': inventario,
        'usuario': request.user.username,
        'sucursal_actual': request.session.get('sucursal_nombre'),
    })


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def api_almacen_buscar(request):
    """Busca productos por código de barras o texto dentro del almacén administrativo."""
    query = request.GET.get('q', '').strip()
    sucursal_id = request.GET.get('sucursal_id')

    if not query or not sucursal_id:
        return JsonResponse({'producto': None})

    producto = Producto.objects.filter(
        Q(codigo_barras__iexact=query) |
        Q(nombre__icontains=query) |
        Q(descripcion__icontains=query)
    ).first()

    if not producto:
        return JsonResponse({'producto': None})

    inventario = InventarioSucursal.objects.filter(
        sucursal_id=sucursal_id,
        producto=producto
    ).first()

    return JsonResponse({'producto': {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion or '',
        'precio': float(producto.precio_venta),
        'codigo_barras': producto.codigo_barras,
        'cantidad': inventario.cantidad if inventario else 0,
        'in_branch': bool(inventario),
        'inventory_id': inventario.id if inventario else None
    }})


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def guardar_producto_almacen(request):
    """Agregar o actualizar un producto en el almacén de una sucursal."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    try:
        data = json.loads(request.body)
        sucursal_id = data.get('sucursal_id')
        codigo_barras = str(data.get('codigo_barras', '')).strip()
        nombre = str(data.get('nombre', '')).strip()
        descripcion = str(data.get('descripcion', '')).strip()
        cantidad = int(data.get('cantidad', 0))
        precio = Decimal(str(data.get('precio', 0)))
        seccion_id = data.get('seccion_id')

        if not sucursal_id or not codigo_barras or not nombre or cantidad < 0 or precio <= 0:
            return JsonResponse({'error': 'Datos incompletos o inválidos'}, status=400)

        sucursal = Sucursal.objects.filter(id=sucursal_id).first()
        if not sucursal:
            return JsonResponse({'error': 'Sucursal no válida'}, status=400)

        producto = Producto.objects.filter(codigo_barras__iexact=codigo_barras).first()
        if producto:
            producto.nombre = nombre
            producto.descripcion = descripcion
            producto.precio_venta = precio
            if seccion_id:
                try:
                    seccion = Seccion.objects.get(id=seccion_id)
                    producto.seccion = seccion
                except Seccion.DoesNotExist:
                    pass
            producto.save()
        else:
            seccion = None
            if seccion_id:
                try:
                    seccion = Seccion.objects.get(id=seccion_id)
                except Seccion.DoesNotExist:
                    pass
            
            producto = Producto.objects.create(
                codigo_barras=codigo_barras,
                nombre=nombre,
                descripcion=descripcion,
                precio_venta=precio,
                seccion=seccion
            )

        inventario = InventarioSucursal.objects.filter(
            sucursal=sucursal,
            producto=producto
        ).first()

        if inventario:
            inventario.cantidad = cantidad
            inventario.save()
            mensaje = 'Producto actualizado en la sucursal.'
        else:
            InventarioSucursal.objects.create(
                sucursal=sucursal,
                producto=producto,
                cantidad=cantidad
            )
            mensaje = 'Producto agregado al almacén de la sucursal.'

        return JsonResponse({'success': True, 'mensaje': mensaje})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def eliminar_producto_almacen(request):
    """Eliminar un producto del inventario de una sucursal."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    try:
        data = json.loads(request.body)
        inventario_id = data.get('inventario_id')

        inventario = InventarioSucursal.objects.filter(id=inventario_id).first()
        if not inventario:
            return JsonResponse({'error': 'Inventario no encontrado'}, status=404)

        inventario.delete()
        return JsonResponse({'success': True, 'mensaje': 'Producto eliminado del inventario de la sucursal.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero')
@solo_activos
def guardar_venta(request):
    """Guardar venta desde AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)
    
    try:
        data = json.loads(request.body)
        detalles = data.get('detalles', [])
        try:
            total = Decimal(str(data.get('total', 0)))
            monto_pagado = Decimal(str(data.get('monto_pagado', 0)))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({'error': 'Total o pago inválido'}, status=400)
        
        sucursal_id = request.session.get('sucursal_id')
        cambio = monto_pagado - total

        if monto_pagado < total:
            return JsonResponse({'error': 'El monto pagado debe ser igual o mayor al total'}, status=400)
        
        if not sucursal_id or not detalles or total <= 0:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        with transaction.atomic():
            venta = Venta.objects.create(
                sucursal_id=sucursal_id,
                usuario=request.user,
                total=total,
                monto_pagado=monto_pagado,
                cambio=cambio
            )
            
            for detalle in detalles:
                producto_id = detalle.get('producto_id')
                try:
                    cantidad = int(detalle.get('cantidad', 0))
                    precio_unitario = Decimal(str(detalle.get('precio_unitario', 0)))
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError('Cantidad o precio inválidos')
                
                if cantidad <= 0 or precio_unitario <= 0:
                    raise ValueError('Cantidad y precio deben ser mayores a cero')
                
                try:
                    producto = Producto.objects.get(id=producto_id)
                except Producto.DoesNotExist:
                    raise ValueError(f'Producto no encontrado: {producto_id}')
                
                try:
                    inventario = InventarioSucursal.objects.get(
                        sucursal_id=sucursal_id,
                        producto=producto
                    )
                except InventarioSucursal.DoesNotExist:
                    raise ValueError('Producto no disponible en la sucursal')
                
                if cantidad > inventario.cantidad:
                    raise ValueError(f'Stock insuficiente para {producto.nombre}')
                
                subtotal = cantidad * precio_unitario
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
                inventario.cantidad -= cantidad
                inventario.save()
        
        return JsonResponse({
            'success': True,
            'venta_id': venta.id,
            'recibo_url': reverse('generar_recibo_venta_html', args=[venta.id]),
            'mensaje': f'Venta #{venta.id} guardada exitosamente',
            'monto_pagado': float(monto_pagado),
            'cambio': float(cambio)
        })
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception:
        return JsonResponse({'error': 'Error interno al guardar la venta'}, status=400)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def generar_recibo_venta(request, venta_id):
    """Generar recibo de venta en formato PDF para impresión térmica."""
    try:
        venta = Venta.objects.select_related('usuario', 'sucursal').get(id=venta_id, sucursal_id=request.session.get('sucursal_id'))
    except Venta.DoesNotExist:
        return HttpResponse('Venta no encontrada', status=404)

    detalles = venta.detalles.select_related('producto').all()
    buffer = BytesIO()
    page_width = 80 * mm
    page_height = 260 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        rightMargin=6,
        leftMargin=6,
        topMargin=10,
        bottomMargin=10,
    )

    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'TicketTitle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,
        spaceAfter=6,
    )
    normal_center = ParagraphStyle(
        'NormalCenter',
        parent=styles['Normal'],
        alignment=1,
        fontSize=8,
        leading=10,
    )
    normal_left = ParagraphStyle(
        'NormalLeft',
        parent=styles['Normal'],
        alignment=0,
        fontSize=8,
        leading=10,
    )

    elements.append(Paragraph('TICKET DE VENTA', title_style))
    elements.append(Paragraph('PUNTO DE VENTA', normal_center))
    elements.append(Paragraph('------------------------------', normal_center))
    elements.append(Paragraph(f'Venta: {venta.id}', normal_left))
    elements.append(Paragraph(f'Usuario: {venta.usuario.username if venta.usuario else "N/A"}', normal_left))
    elements.append(Paragraph(f'Sucursal: {venta.sucursal.nombre}', normal_left))
    elements.append(Paragraph(f'Fecha: {venta.fecha.strftime("%d/%m/%Y %H:%M")}', normal_left))
    elements.append(Paragraph('------------------------------', normal_center))

    table_data = [[
        Paragraph('<b>C</b>', normal_left),
        Paragraph('<b>Producto</b>', normal_left),
        Paragraph('<b>P.U.</b>', normal_left),
        Paragraph('<b>Total</b>', normal_left)
    ]]

    for detalle in detalles:
        nombre = detalle.producto.nombre[:18]
        table_data.append([
            Paragraph(str(detalle.cantidad), normal_left),
            Paragraph(nombre, normal_left),
            Paragraph(f'${detalle.precio_unitario:.2f}', normal_left),
            Paragraph(f'${detalle.subtotal:.2f}', normal_left)
        ])

    table = Table(table_data, colWidths=[10*mm, 34*mm, 18*mm, 18*mm])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
    ]))
    elements.append(table)
    elements.append(Paragraph('------------------------------', normal_center))
    elements.append(Paragraph(f'Monto pagado: ${venta.monto_pagado:.2f}', normal_left))
    elements.append(Paragraph(f'Cambio: ${venta.cambio:.2f}', normal_left))
    elements.append(Paragraph('------------------------------', normal_center))
    elements.append(Paragraph(f'TOTAL: ${venta.total:.2f}', ParagraphStyle('TotalStyle', parent=styles['Normal'], fontSize=10, alignment=1, leading=12)))
    elements.append(Paragraph('Gracias por su compra', normal_center))
    elements.append(Paragraph('------------------------------', normal_center))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_venta_{venta.id}.pdf"'
    return response


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def generar_recibo_venta_html(request, venta_id):
    """Generar recibo de venta en HTML y disparar impresión automática."""
    try:
        venta = Venta.objects.select_related('usuario', 'sucursal').get(id=venta_id, sucursal_id=request.session.get('sucursal_id'))
    except Venta.DoesNotExist:
        return HttpResponse('Venta no encontrada', status=404)

    detalles = venta.detalles.select_related('producto').all()
    return render(request, 'recibo_venta.html', {
        'venta': venta,
        'detalles': detalles,
    })


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def corte_caja(request):
    """Vista para realizar corte de caja"""
    sucursal_id = request.session.get('sucursal_id')
    
    # Obtener corte abierto actual
    corte_abierto = CorteCaja.objects.filter(
        sucursal_id=sucursal_id,
        estado='abierto',
        usuario=request.user
    ).first()
    
    # Obtener ventas del corte actual
    ventas_corte = []
    total_ventas = 0
    corte_apertura = None
    
    if corte_abierto:
        apertura_corte = corte_abierto.fecha_apertura
        ultimo_corte_cerrado = CorteCaja.objects.filter(
            sucursal_id=sucursal_id,
            usuario=request.user,
            estado='cerrado'
        ).order_by('-fecha_cierre').first()

        if ultimo_corte_cerrado:
            ventas_anteriores = Venta.objects.filter(
                sucursal_id=sucursal_id,
                usuario=request.user,
                fecha__gt=ultimo_corte_cerrado.fecha_cierre,
                fecha__lt=corte_abierto.fecha_apertura
            ).order_by('fecha')
        else:
            ventas_anteriores = Venta.objects.filter(
                sucursal_id=sucursal_id,
                usuario=request.user,
                fecha__lt=corte_abierto.fecha_apertura
            ).order_by('fecha')

        if ventas_anteriores.exists():
            apertura_corte = ventas_anteriores.first().fecha
        else:
            apertura_corte = corte_abierto.fecha_apertura

        ventas_corte = Venta.objects.filter(
            sucursal_id=sucursal_id,
            usuario=request.user,
            fecha__gte=apertura_corte,
            fecha__lte=timezone.now()
        ).order_by('-fecha')
        total_ventas = ventas_corte.aggregate(Sum('total'))['total__sum'] or 0
        corte_apertura = apertura_corte
    
    context = {
        'corte_abierto': corte_abierto,
        'ventas_corte': ventas_corte,
        'total_ventas': total_ventas,
        'sucursal': request.session.get('sucursal_nombre'),
        'usuario': request.user.username,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'corte_caja.html', context)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def abrir_corte(request):
    """Abrir nuevo corte de caja"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)
    
    try:
        data = json.loads(request.body)
        monto_inicial = float(data.get('monto_inicial', 0))
        sucursal_id = request.session.get('sucursal_id')
        
        # Cerrar cortes anteriores abiertos
        CorteCaja.objects.filter(
            sucursal_id=sucursal_id,
            usuario=request.user,
            estado='abierto'
        ).update(estado='cerrado', fecha_cierre=timezone.now())

        apertura = timezone.now()
        ultimo_corte_cerrado = CorteCaja.objects.filter(
            sucursal_id=sucursal_id,
            usuario=request.user,
            estado='cerrado'
        ).order_by('-fecha_cierre').first()

        if ultimo_corte_cerrado:
            primera_venta_posterior = Venta.objects.filter(
                sucursal_id=sucursal_id,
                usuario=request.user,
                fecha__gt=ultimo_corte_cerrado.fecha_cierre
            ).order_by('fecha').first()
        else:
            primera_venta_posterior = Venta.objects.filter(
                sucursal_id=sucursal_id,
                usuario=request.user
            ).order_by('fecha').first()

        if primera_venta_posterior:
            apertura = primera_venta_posterior.fecha
        
        # Crear nuevo corte
        corte = CorteCaja.objects.create(
            sucursal_id=sucursal_id,
            usuario=request.user,
            fecha_apertura=apertura,
            monto_inicial=monto_inicial,
            estado='abierto'
        )
        
        return JsonResponse({
            'success': True,
            'corte_id': corte.id,
            'mensaje': 'Corte de caja abierto exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def cerrar_corte(request):
    """Cerrar corte de caja"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)
    
    try:
        data = json.loads(request.body)
        corte_id = data.get('corte_id')
        notas = data.get('notas', '')
        
        corte = CorteCaja.objects.get(id=corte_id, usuario=request.user)
        
        # Calcular total de ventas
        ventas = Venta.objects.filter(
            sucursal_id=corte.sucursal_id,
            usuario=request.user,
            fecha__gte=corte.fecha_apertura,
            fecha__lte=timezone.now()
        )
        total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
        
        corte.total_ventas = total_ventas
        corte.total_efectivo = corte.monto_inicial + total_ventas
        corte.estado = 'cerrado'
        corte.fecha_cierre = timezone.now()
        corte.notas = notas
        corte.save()
        
        return JsonResponse({
            'success': True,
            'corte_id': corte.id,
            'mensaje': 'Corte de caja cerrado exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def generar_pdf_corte(request, corte_id):
    """Generar PDF del corte de caja"""
    try:
        corte = CorteCaja.objects.get(id=corte_id, usuario=request.user)
    except CorteCaja.DoesNotExist:
        return HttpResponse('Corte no encontrado', status=404)
    
    # Obtener ventas del corte
    ventas = Venta.objects.filter(
        sucursal_id=corte.sucursal_id,
        usuario=request.user,
        fecha__gte=corte.fecha_apertura,
        fecha__lte=corte.fecha_cierre or timezone.now()
    )
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Encabezado
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        alignment=1  # center
    )
    
    elements.append(Paragraph("CORTE DE CAJA", title_style))
    elements.append(Spacer(1, 12))
    
    # Información general
    info_data = [
        ['Sucursal:', corte.sucursal.nombre],
        ['Usuario:', corte.usuario.username],
        ['Fecha Apertura:', corte.fecha_apertura.strftime('%d/%m/%Y %H:%M')],
        ['Fecha Cierre:', corte.fecha_cierre.strftime('%d/%m/%Y %H:%M') if corte.fecha_cierre else 'Abierto'],
        ['Estado:', corte.get_estado_display()],
    ]
    
    info_table = Table(info_data, colWidths=[200, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Tabla de ventas
    elements.append(Paragraph("Detalle de Ventas", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    ventas_data = [['ID', 'Usuario', 'Hora', 'Total']]
    total_vtas = 0
    
    for venta in ventas:
        ventas_data.append([
            str(venta.id),
            venta.usuario.username if venta.usuario else 'N/A',
            venta.fecha.strftime('%H:%M:%S'),
            f'${venta.total:.2f}'
        ])
        total_vtas += venta.total
    
    ventas_data.append(['', '', 'TOTAL:', f'${total_vtas:.2f}'])
    
    ventas_table = Table(ventas_data, colWidths=[60, 150, 100, 100])
    ventas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    elements.append(ventas_table)
    elements.append(Spacer(1, 20))
    
    # Resumen
    resumen_data = [
        ['Monto Inicial:', f"${corte.monto_inicial:.2f}"],
        ['Total Ventas:', f"${corte.total_ventas:.2f}"],
        ['Total Efectivo:', f"${corte.total_efectivo:.2f}"],
    ]
    
    resumen_table = Table(resumen_data, colWidths=[200, 300])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(resumen_table)
    
    # Notas
    if corte.notas:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Notas:", styles['Heading3']))
        elements.append(Paragraph(corte.notas, styles['Normal']))
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="corte_caja_{corte.id}.pdf"'
    return response


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def consultar_inventario(request):
    """Consultar disponibilidad de productos en existencia"""
    sucursal_id = request.session.get('sucursal_id')
    seccion_id = request.GET.get('seccion')
    
    # Obtener todas las secciones
    from inventario.models import Seccion
    secciones = Seccion.objects.all().order_by('nombre')
    
    # Obtener inventario
    inventario = InventarioSucursal.objects.filter(
        sucursal_id=sucursal_id
    ).select_related('producto', 'producto__seccion').order_by('producto__nombre')
    
    # Filtrar por sección si se especifica
    if seccion_id:
        inventario = inventario.filter(producto__seccion_id=seccion_id)
    
    context = {
        'inventario': inventario,
        'secciones': secciones,
        'seccion_seleccionada': int(seccion_id) if seccion_id else None,
        'sucursal': request.session.get('sucursal_nombre'),
        'usuario': request.user.username,
    }
    
    return render(request, 'consultar_inventario.html', context)


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def imprimir_seccion_inventario(request, seccion_id):
    """Generar PDF de inventario por sección para impresora térmica (80mm)"""
    sucursal_id = request.session.get('sucursal_id')
    
    try:
        seccion = Seccion.objects.get(id=seccion_id)
    except Seccion.DoesNotExist:
        return HttpResponse('Sección no encontrada', status=404)
    
    # Obtener inventario de la sección
    inventario = InventarioSucursal.objects.filter(
        sucursal_id=sucursal_id,
        producto__seccion=seccion,
        cantidad__gt=0
    ).select_related('producto').order_by('producto__nombre')
    
    # Crear PDF para impresora térmica (80mm de ancho)
    buffer = BytesIO()
    page_width = 80 * mm
    page_height = 200 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        rightMargin=4,
        leftMargin=4,
        topMargin=8,
        bottomMargin=8,
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Estilos para thermal printer
    title_style = ParagraphStyle(
        'TicketTitle',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        spaceAfter=3,
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=8,
        leading=8,
        alignment=0,
    )
    
    # Encabezado
    elements.append(Paragraph('INVENTARIO', title_style))
    elements.append(Paragraph(f'SECCIÓN: {seccion.nombre}', subtitle_style))
    elements.append(Paragraph(f'Sucursal: {request.session.get("sucursal_nombre")}', normal_style))
    from datetime import datetime
    elements.append(Paragraph(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', normal_style))
    elements.append(Paragraph('─' * 30, subtitle_style))
    
    # Tabla de productos
    table_data = [[
        Paragraph('<b>Cant</b>', normal_style),
        Paragraph('<b>Producto</b>', normal_style),
        Paragraph('<b>Precio</b>', normal_style)
    ]]
    
    total_productos = 0
    for item in inventario:
        nombre_corto = item.producto.nombre[:16]
        table_data.append([
            Paragraph(str(item.cantidad), normal_style),
            Paragraph(nombre_corto, normal_style),
            Paragraph(f'${item.producto.precio_venta:.2f}', normal_style)
        ])
        total_productos += item.cantidad
    
    if not inventario.exists():
        table_data.append([
            Paragraph('', normal_style),
            Paragraph('Sin productos', normal_style),
            Paragraph('', normal_style)
        ])
    
    table = Table(table_data, colWidths=[12*mm, 40*mm, 18*mm])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Paragraph('─' * 30, subtitle_style))
    
    # Totales
    elements.append(Paragraph(f'Total de artículos: {total_productos}', ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        fontName='Helvetica-Bold',
        leading=8
    )))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="inventario_{seccion.nombre}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


@login_required(login_url='login')
@rol_requerido('vendedor', 'cajero', 'admin')
@solo_activos
def api_inventario(request):
    """API para buscar productos en inventario"""
    query = request.GET.get('q', '').strip()
    sucursal_id = request.session.get('sucursal_id')
    
    if not query or len(query) < 2:
        return JsonResponse({'productos': []})
    
    inventario = InventarioSucursal.objects.filter(
        sucursal_id=sucursal_id
    ).filter(
        Q(producto__nombre__icontains=query) |
        Q(producto__descripcion__icontains=query) |
        Q(producto__codigo_barras__icontains=query)
    ).select_related('producto')[:15]
    
    resultado = []
    for item in inventario:
        resultado.append({
            'nombre': item.producto.nombre,
            'codigo': item.producto.codigo_barras or 'Sin código',
            'precio': float(item.producto.precio_venta),
            'cantidad': item.cantidad,
            'estado': 'En stock' if item.cantidad > 0 else 'Sin stock'
        })
    
    return JsonResponse({'productos': resultado})


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def actualizar_cantidad_almacen(request):
    """Actualizar cantidad de producto en el almacén de una sucursal."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    try:
        data = json.loads(request.body)
        inventory_id = data.get('inventory_id')
        nueva_cantidad = int(data.get('cantidad', 0))

        if nueva_cantidad < 0:
            return JsonResponse({'error': 'La cantidad no puede ser negativa'}, status=400)

        inventario = InventarioSucursal.objects.filter(id=inventory_id).first()
        if not inventario:
            return JsonResponse({'error': 'Inventario no encontrado'}, status=404)

        inventario.cantidad = nueva_cantidad
        inventario.save()

        return JsonResponse({
            'success': True,
            'mensaje': 'Cantidad actualizada correctamente',
            'nueva_cantidad': inventario.cantidad
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def actualizar_precio_almacen(request):
    """Actualizar precio de un producto."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        nuevo_precio = Decimal(str(data.get('precio', 0)))

        if nuevo_precio <= 0:
            return JsonResponse({'error': 'El precio debe ser mayor a cero'}, status=400)

        producto = Producto.objects.filter(id=producto_id).first()
        if not producto:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)

        producto.precio_venta = nuevo_precio
        producto.save()

        return JsonResponse({
            'success': True,
            'mensaje': 'Precio actualizado correctamente',
            'nuevo_precio': float(nuevo_precio)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='login')
@rol_requerido('admin')
@solo_activos
def actualizar_descripcion_almacen(request):
    """Actualizar descripción de un producto."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=400)

    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        nueva_descripcion = str(data.get('descripcion', '')).strip()

        producto = Producto.objects.filter(id=producto_id).first()
        if not producto:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)

        producto.descripcion = nueva_descripcion
        producto.save()

        return JsonResponse({
            'success': True,
            'mensaje': 'Descripción actualizada correctamente',
            'nueva_descripcion': nueva_descripcion
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
