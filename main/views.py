from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from .models import Cliente, Credito, Pago, Codeudor, CronogramaPago, Cobrador, Ruta, TareaCobro
from .forms import ClienteForm, CreditoForm, PagoForm, CodeudorForm

# Para generar PDFs
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime, timedelta, date
from io import BytesIO

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos'})
    
    return render(request, 'login.html')

def force_login_view(request):
    """Vista para forzar mostrar el login incluso si hay sesión activa"""
    logout(request)  # Cerrar cualquier sesión existente
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos'})
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Obtener estadísticas
    total_clientes = Cliente.objects.filter(activo=True).count()
    total_creditos = Credito.objects.exclude(estado='PAGADO').count()
    total_pagos = Pago.objects.count()
    creditos_vencidos = Credito.objects.filter(estado='VENCIDO').count()
    
    # Montos
    monto_total_prestado = Credito.objects.filter(estado__in=['APROBADO', 'DESEMBOLSADO']).aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    monto_total_recaudado = Pago.objects.aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    context = {
        'total_clientes': total_clientes,
        'total_creditos': total_creditos,
        'total_pagos': total_pagos,
        'creditos_vencidos': creditos_vencidos,
        'monto_total_prestado': monto_total_prestado,
        'monto_total_recaudado': monto_total_recaudado,
        'actividad_reciente': [],  # Por ahora vacío
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def clientes(request):
    from django.core.paginator import Paginator
    
    clientes_list = Cliente.objects.filter(activo=True).order_by('-fecha_registro')
    
    # Paginación: 20 clientes por página
    paginator = Paginator(clientes_list, 20)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)
    
    return render(request, 'clientes.html', {'clientes': clientes})

@login_required
def creditos(request):
    from django.core.paginator import Paginator
    
    creditos_list = Credito.objects.all().order_by('-fecha_solicitud')
    
    # Calcular estadísticas (usar la lista completa)
    total_creditos = creditos_list.count()
    creditos_aprobados = creditos_list.filter(estado='APROBADO').count()
    creditos_pendientes = creditos_list.filter(estado='SOLICITADO').count()
    creditos_vencidos = creditos_list.filter(estado='VENCIDO').count()
    creditos_desembolsados = creditos_list.filter(estado='DESEMBOLSADO').count()
    creditos_pagados = creditos_list.filter(estado='PAGADO').count()
    
    # Paginación: 15 créditos por página
    paginator = Paginator(creditos_list, 15)
    page_number = request.GET.get('page')
    creditos = paginator.get_page(page_number)
    
    context = {
        'creditos': creditos,
        'total_creditos': total_creditos,
        'creditos_aprobados': creditos_aprobados,
        'creditos_pendientes': creditos_pendientes,
        'creditos_vencidos': creditos_vencidos,
        'creditos_desembolsados': creditos_desembolsados,
        'creditos_pagados': creditos_pagados,
    }
    return render(request, 'creditos.html', context)

@login_required
def pagos(request):
    from django.db.models import Sum
    from datetime import date, datetime, timedelta
    from django.utils import timezone
    from django.core.paginator import Paginator
    
    pagos_list = Pago.objects.all().order_by('-fecha_pago')
    
    # Calcular estadísticas (usar la lista completa)
    total_pagos = pagos_list.count()
    
    # Pagos de hoy
    hoy = timezone.now().date()
    pagos_hoy = pagos_list.filter(fecha_pago__date=hoy).count()
    
    # Monto recaudado hoy
    recaudado_hoy = pagos_list.filter(fecha_pago__date=hoy).aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    # Promedio mensual (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    pagos_mes = pagos_list.filter(fecha_pago__gte=hace_30_dias)
    promedio_mensual = pagos_mes.aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    # Total recaudado histórico
    total_recaudado = pagos_list.aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    # Promedio por pago
    promedio_pago = total_recaudado / total_pagos if total_pagos > 0 else 0
    
    # Paginación: 25 pagos por página
    paginator = Paginator(pagos_list, 25)
    page_number = request.GET.get('page')
    pagos = paginator.get_page(page_number)
    
    context = {
        'pagos': pagos,
        'total_pagos': total_pagos,
        'pagos_hoy': pagos_hoy,
        'recaudado_hoy': recaudado_hoy,
        'promedio_mensual': promedio_mensual,
        'total_recaudado': total_recaudado,
        'promedio_pago': promedio_pago,
    }
    
    return render(request, 'pagos.html', context)

# CRUD Clientes
@login_required
def nuevo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            cliente = form.save()
            
            # Debug: Mostrar archivos recibidos
            archivos_recibidos = []
            for field_name in ['foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera', 'foto_recibo_servicio']:
                if field_name in request.FILES:
                    archivo = request.FILES[field_name]
                    archivos_recibidos.append(f'{field_name}: {archivo.name} ({archivo.size} bytes)')
            
            if archivos_recibidos:
                print(f'Archivos guardados para {cliente.nombre_completo}:')
                for archivo in archivos_recibidos:
                    print(f'  - {archivo}')
            
            messages.success(request, f'Cliente {cliente.nombre_completo} creado exitosamente')
            return redirect('detalle_cliente', cliente_id=cliente.id)  # Redirigir al detalle para ver los documentos
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ClienteForm()
    return render(request, 'nuevo_cliente.html', {'form': form})

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            cliente_actualizado = form.save()
            
            # Debug: Mostrar archivos recibidos
            archivos_recibidos = []
            for field_name in ['foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera', 'foto_recibo_servicio']:
                if field_name in request.FILES:
                    archivo = request.FILES[field_name]
                    archivos_recibidos.append(f'{field_name}: {archivo.name} ({archivo.size} bytes)')
            
            if archivos_recibidos:
                print(f'Archivos actualizados para {cliente_actualizado.nombre_completo}:')
                for archivo in archivos_recibidos:
                    print(f'  - {archivo}')
            
            messages.success(request, f'Cliente {cliente_actualizado.nombre_completo} actualizado exitosamente')
            return redirect('detalle_cliente', cliente_id=cliente.id)
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'editar_cliente.html', {'form': form, 'cliente': cliente})

@login_required
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        messages.success(request, f'Cliente {cliente.nombre_completo} desactivado exitosamente')
        return redirect('clientes')
    return render(request, 'confirmar_eliminar_cliente.html', {'cliente': cliente})

# CRUD Créditos
@login_required
def nuevo_credito(request):
    if request.method == 'POST':
        form = CreditoForm(request.POST)
        if form.is_valid():
            # Obtener el cliente del cleaned_data
            cliente = form.cleaned_data.get('cliente')
            if not cliente:
                messages.error(request, 'Error: No se pudo identificar el cliente.')
                return render(request, 'nuevo_credito.html', {'form': form})
            
            # Crear el crédito pero no guardar aún
            credito = form.save(commit=False)
            credito.cliente = cliente  # Asegurar que el cliente esté asignado
            credito.save()  # Ahora sí guardar
            
            # Mostrar información del crédito creado
            messages.success(
                request, 
                f'¡Crédito #{credito.id} creado exitosamente para {credito.cliente.nombre_completo}!'
            )
            messages.info(
                request,
                f'Monto: ${credito.monto:,.2f} | '
                f'Cuotas: {credito.cantidad_cuotas} {credito.get_tipo_plazo_display().lower()}s | '
                f'Valor cuota: ${credito.valor_cuota:,.2f}'
            )
            return redirect('creditos')
        else:
            # Mostrar errores de validación detallados
            for field, errors in form.errors.items():
                field_label = form.fields.get(field, {}).label or field
                for error in errors:
                    messages.error(request, f'{field_label}: {error}')
    else:
        form = CreditoForm()
    return render(request, 'nuevo_credito.html', {'form': form})

@login_required
def editar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id)
    if request.method == 'POST':
        form = CreditoForm(request.POST, instance=credito)
        if form.is_valid():
            form.save()
            messages.success(request, f'Crédito #{credito.id} actualizado exitosamente')
            return redirect('creditos')
    else:
        form = CreditoForm(instance=credito)
    return render(request, 'editar_credito.html', {'form': form, 'credito': credito})

# CRUD Pagos
@login_required
def nuevo_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        
        # Actualizar queryset del crédito basado en la cédula proporcionada
        cedula_cliente = request.POST.get('cedula_cliente')
        if cedula_cliente:
            try:
                cliente = Cliente.objects.get(cedula=cedula_cliente, activo=True)
                form.fields['credito'].queryset = Credito.objects.filter(
                    cliente=cliente,
                    estado__in=['APROBADO', 'DESEMBOLSADO']
                ).exclude(estado='PAGADO')
            except Cliente.DoesNotExist:
                pass
        
        if form.is_valid():
            pago = form.save()
            credito = pago.credito
            
            # Actualizar estado del crédito si está completamente pagado
            if credito.esta_al_dia():
                credito.estado = 'PAGADO'
                credito.save()
                messages.success(
                    request, 
                    f'Pago #{pago.id} registrado exitosamente. '
                    f'¡El crédito #{credito.id} de {credito.cliente.nombre_completo} está completamente pagado!'
                )
            else:
                saldo = credito.saldo_pendiente()
                messages.success(
                    request, 
                    f'Pago #{pago.id} registrado exitosamente. '
                    f'Saldo pendiente: ${saldo}'
                )
            # Redirigir a página de confirmación con el pago recién creado
            messages.success(
                request,
                f'¡Pago registrado exitosamente! Puede descargar o enviar el recibo al cliente.'
            )
            return redirect('confirmacion_pago', pago_id=pago.id)
        else:
            # Si hay errores, mostrarlos como mensajes
            for error in form.non_field_errors():
                messages.error(request, error)
            
            # Mostrar errores de campo específicos
            for field, errors in form.errors.items():
                if field == '__all__':
                    for error in errors:
                        messages.error(request, error)
                else:
                    field_label = form.fields.get(field, None)
                    if field_label and hasattr(field_label, 'label'):
                        label = field_label.label or field
                    else:
                        label = field
                    for error in errors:
                        messages.error(request, f'{label}: {error}')
    else:
        form = PagoForm()
    
    # Obtener información de créditos para mostrar en el template
    creditos_info = []
    for credito in Credito.objects.filter(estado__in=['APROBADO', 'DESEMBOLSADO']).exclude(estado='PAGADO'):
        if credito.puede_recibir_pagos():
            creditos_info.append({
                'id': credito.id,
                'cliente': credito.cliente.nombre_completo,
                'monto_total': credito.monto,
                'total_pagado': credito.total_pagado(),
                'saldo_pendiente': credito.saldo_pendiente()
            })
    
    return render(request, 'nuevo_pago.html', {
        'form': form,
        'creditos_info': creditos_info
    })

# Vistas para cambio de estado de créditos
@login_required
def aprobar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id)
    
    if credito.estado != 'SOLICITADO':
        messages.error(request, f'El crédito #{credito.id} no está en estado SOLICITADO')
        return redirect('creditos')
    
    # Aquí podrías agregar lógica de validación créditicia
    # Por ejemplo: verificar ingresos, historial crediticio, etc.
    
    credito.estado = 'APROBADO'
    credito.fecha_aprobacion = timezone.now()
    credito.save()
    
    messages.success(
        request, 
        f'¡Crédito #{credito.id} de {credito.cliente.nombre_completo} por ${credito.monto} APROBADO exitosamente!'
    )
    return redirect('creditos')

@login_required
def rechazar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id)
    
    if credito.estado != 'SOLICITADO':
        messages.error(request, f'El crédito #{credito.id} no está en estado SOLICITADO')
        return redirect('creditos')
    
    credito.estado = 'RECHAZADO'
    credito.save()
    
    messages.warning(
        request, 
        f'Crédito #{credito.id} de {credito.cliente.nombre_completo} RECHAZADO'
    )
    return redirect('creditos')

@login_required
def desembolsar_credito(request, credito_id):
    credito = get_object_or_404(Credito, id=credito_id)
    
    if credito.estado != 'APROBADO':
        messages.error(request, f'El crédito #{credito.id} no está en estado APROBADO')
        return redirect('creditos')
    
    # Actualizar estado y fecha de desembolso
    credito.estado = 'DESEMBOLSADO'
    credito.fecha_desembolso = timezone.now()
    credito.save()
    
    # Generar cronograma de pagos
    try:
        credito.generar_cronograma()
        cronograma_creado = True
        total_cuotas = credito.cronograma.count()
    except Exception as e:
        cronograma_creado = False
        messages.warning(request, f'Error al generar cronograma: {str(e)}')
    
    # Mensaje de éxito
    messages.success(
        request, 
        f'¡Desembolso de ${credito.monto:,.2f} realizado exitosamente a {credito.cliente.nombre_completo}!'
    )
    
    if cronograma_creado:
        messages.info(
            request,
            f'Cronograma generado: {total_cuotas} cuotas {credito.get_tipo_plazo_display().lower()}s '
            f'de ${credito.valor_cuota:,.2f} cada una. '
            f'Primera cuota vence: {credito.cronograma.first().fecha_vencimiento.strftime("%d/%m/%Y")}'
        )
    
    return redirect('creditos')

# Vistas para Codeudores
@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    try:
        codeudor = cliente.codeudor
    except Codeudor.DoesNotExist:
        codeudor = None
    
    creditos = cliente.credito_set.all().order_by('-fecha_solicitud')
    
    context = {
        'cliente': cliente,
        'codeudor': codeudor,
        'creditos': creditos,
    }
    return render(request, 'detalle_cliente.html', context)

@login_required
def nuevo_codeudor(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Verificar si ya tiene codeudor
    try:
        cliente.codeudor
        messages.error(request, f'El cliente {cliente.nombre_completo} ya tiene un codeudor asignado')
        return redirect('detalle_cliente', cliente_id=cliente.id)
    except Codeudor.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = CodeudorForm(request.POST, request.FILES)
        if form.is_valid():
            codeudor = form.save(commit=False)
            codeudor.cliente = cliente
            codeudor.save()
            messages.success(request, f'Codeudor {codeudor.nombre_completo} creado exitosamente para {cliente.nombre_completo}')
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = CodeudorForm()
    
    return render(request, 'nuevo_codeudor.html', {'form': form, 'cliente': cliente})

@login_required
def editar_codeudor(request, codeudor_id):
    codeudor = get_object_or_404(Codeudor, id=codeudor_id)
    
    if request.method == 'POST':
        form = CodeudorForm(request.POST, request.FILES, instance=codeudor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Codeudor {codeudor.nombre_completo} actualizado exitosamente')
            return redirect('detalle_cliente', cliente_id=codeudor.cliente.id)
    else:
        form = CodeudorForm(instance=codeudor)
    
    return render(request, 'editar_codeudor.html', {'form': form, 'codeudor': codeudor})

@login_required
def eliminar_codeudor(request, codeudor_id):
    codeudor = get_object_or_404(Codeudor, id=codeudor_id)
    cliente = codeudor.cliente
    
    if request.method == 'POST':
        codeudor.delete()
        messages.success(request, f'Codeudor {codeudor.nombre_completo} eliminado exitosamente')
        return redirect('detalle_cliente', cliente_id=cliente.id)
    
    return render(request, 'confirmar_eliminar_codeudor.html', {'codeudor': codeudor})

# API para búsqueda de clientes
@login_required
def buscar_cliente(request):
    """Vista AJAX para buscar cliente por cédula"""
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({
            'success': False,
            'error': 'Cédula no proporcionada'
        })
    
    try:
        cliente = Cliente.objects.get(cedula=cedula, activo=True)
        
        # Obtener URL de la foto si existe
        foto_rostro_url = None
        if cliente.foto_rostro:
            foto_rostro_url = cliente.foto_rostro.url
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombres': cliente.nombres,
                'apellidos': cliente.apellidos,
                'cedula': cliente.cedula,
                'celular': cliente.celular,
                'direccion': cliente.direccion,
                'barrio': cliente.barrio,
                'foto_rostro': foto_rostro_url,
            }
        })
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No se encontró un cliente activo con cédula "{cedula}"'
        })

# Vista de confirmación de pago
@login_required
def confirmacion_pago(request, pago_id):
    """Vista para mostrar confirmación de pago con opciones de descarga/envío"""
    pago = get_object_or_404(Pago, id=pago_id)
    credito = pago.credito
    cliente = credito.cliente
    
    # Calcular información adicional de forma más robusta
    try:
        # Intentar usar cronograma si existe
        if hasattr(credito, 'cronograma') and credito.cronograma.exists():
            cuotas_pagadas = credito.cronograma.filter(estado='PAGADO').count()
        else:
            # Calcular basado en pagos y valor de cuota
            total_pagado = credito.total_pagado()
            valor_cuota = credito.valor_cuota if credito.valor_cuota > 0 else 1
            cuotas_pagadas = int(total_pagado / valor_cuota)
            
        total_cuotas = credito.cantidad_cuotas if credito.cantidad_cuotas else 1
        progreso_pago = (cuotas_pagadas / total_cuotas) * 100 if total_cuotas > 0 else 0
        progreso_pago = min(100, max(0, progreso_pago))  # Limitar entre 0 y 100
        
    except Exception:
        cuotas_pagadas = 0
        total_cuotas = credito.cantidad_cuotas if credito.cantidad_cuotas else 1
        progreso_pago = 0
    
    # Calcular próxima fecha de pago (estimada)
    proxima_fecha_pago = None
    if cuotas_pagadas < total_cuotas:
        from datetime import timedelta
        if credito.tipo_plazo == 'DIARIO':
            proxima_fecha_pago = pago.fecha_pago.date() + timedelta(days=1)
        elif credito.tipo_plazo == 'SEMANAL':
            proxima_fecha_pago = pago.fecha_pago.date() + timedelta(weeks=1)
        elif credito.tipo_plazo == 'QUINCENAL':
            proxima_fecha_pago = pago.fecha_pago.date() + timedelta(days=15)
        elif credito.tipo_plazo == 'MENSUAL':
            fecha_pago = pago.fecha_pago.date()
            mes = fecha_pago.month + 1
            año = fecha_pago.year
            if mes > 12:
                mes = 1
                año += 1
            try:
                proxima_fecha_pago = fecha_pago.replace(year=año, month=mes)
            except ValueError:
                # Manejar casos como 31 de marzo -> 30 de abril
                from calendar import monthrange
                ultimo_dia = monthrange(año, mes)[1]
                proxima_fecha_pago = fecha_pago.replace(year=año, month=mes, day=min(fecha_pago.day, ultimo_dia))
    
    context = {
        'pago': pago,
        'credito': credito,
        'cliente': cliente,
        'cuotas_pagadas': cuotas_pagadas,
        'total_cuotas': total_cuotas,
        'progreso_pago': progreso_pago,
        'proxima_fecha_pago': proxima_fecha_pago,
        'credito_completado': credito.estado == 'PAGADO'
    }
    
    return render(request, 'confirmacion_pago.html', context)

# Vista para búsqueda AJAX de clientes en formulario de crédito
@login_required
def buscar_cliente_credito(request):
    """Vista AJAX para buscar cliente por cédula en el formulario de crédito"""
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({
            'success': False,
            'error': 'Debe proporcionar una cédula'
        })
    
    try:
        cliente = Cliente.objects.get(cedula=cedula, activo=True)
        
        # Preparar URL de la foto (si existe)
        foto_url = None
        if cliente.foto_rostro:
            try:
                foto_url = cliente.foto_rostro.url
            except ValueError:
                foto_url = None
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre_completo': cliente.nombre_completo,
                'cedula': cliente.cedula,
                'celular': cliente.celular,
                'direccion': cliente.direccion,
                'foto_url': foto_url
            }
        })
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No se encontró un cliente activo con cédula "{cedula}"'
        })

# Vista para obtener datos del crédito para el modal de aprobación
@login_required
def obtener_datos_credito(request, credito_id):
    """Vista AJAX para obtener datos completos del crédito"""
    try:
        credito = get_object_or_404(Credito, id=credito_id)
        
        # Calcular fechas del cronograma (simulado)
        fechas_cronograma = []
        if credito.cantidad_cuotas > 0:
            fecha_base = timezone.now().date()
            
            for i in range(credito.cantidad_cuotas):
                if credito.tipo_plazo == 'DIARIO':
                    fecha_pago = fecha_base + timedelta(days=i+1)
                elif credito.tipo_plazo == 'SEMANAL':
                    fecha_pago = fecha_base + timedelta(weeks=i+1)
                elif credito.tipo_plazo == 'QUINCENAL':
                    fecha_pago = fecha_base + timedelta(days=(i+1)*15)
                else:  # MENSUAL
                    mes = fecha_base.month + (i + 1)
                    año = fecha_base.year
                    while mes > 12:
                        mes -= 12
                        año += 1
                    
                    try:
                        fecha_pago = fecha_base.replace(year=año, month=mes)
                    except ValueError:
                        from calendar import monthrange
                        ultimo_dia = monthrange(año, mes)[1]
                        fecha_pago = fecha_base.replace(year=año, month=mes, day=min(fecha_base.day, ultimo_dia))
                
                fechas_cronograma.append({
                    'cuota': i + 1,
                    'fecha': fecha_pago.strftime('%d/%m/%Y'),
                    'valor': float(credito.valor_cuota)
                })
        
        return JsonResponse({
            'success': True,
            'credito': {
                'id': credito.id,
                'cliente': {
                    'nombre_completo': credito.cliente.nombre_completo,
                    'cedula': credito.cliente.cedula,
                    'celular': credito.cliente.celular,
                    'direccion': credito.cliente.direccion,
                },
                'monto': float(credito.monto),
                'tasa_interes': float(credito.tasa_interes),
                'tipo_plazo': credito.get_tipo_plazo_display(),
                'cantidad_cuotas': credito.cantidad_cuotas,
                'valor_cuota': float(credito.valor_cuota),
                'monto_total': float(credito.monto_total),
                'total_interes': float(credito.total_interes),
                'fecha_solicitud': credito.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
                'descripcion_pago': credito.descripcion_pago,
                'cronograma': fechas_cronograma
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Vista para generar PDF del cronograma
@login_required
def generar_pdf_cronograma(request, credito_id):
    """Genera PDF del cronograma de pagos optimizado para una sola página"""
    credito = get_object_or_404(Credito, id=credito_id)
    
    # Crear buffer para el PDF con márgenes más pequeños
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    # Estilos optimizados para menos espacio
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=12,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=8,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3
    )
    
    # Contenido del PDF
    story = []
    
    # Título principal compacto
    story.append(Paragraph("SISTEMA DE CRÉDITOS - CRONOGRAMA DE PAGOS", title_style))
    story.append(Spacer(1, 8))
    
    # Información del crédito (sin tasa de interés anual)
    info_credito = [
        ["Crédito N°:", f"#{credito.id:04d}", "Cliente:", credito.cliente.nombre_completo],
        ["Cédula:", credito.cliente.cedula, "Celular:", credito.cliente.celular],
        ["Fecha:", credito.fecha_solicitud.strftime('%d/%m/%Y'), "Modalidad:", credito.get_tipo_plazo_display()],
        ["Monto:", f"${credito.monto:,.0f}", "Cuotas:", f"{credito.cantidad_cuotas}"],
        ["Valor Cuota:", f"${credito.valor_cuota:,.0f}", "Total:", f"${credito.monto_total:,.0f}"]
    ]
    
    info_table = Table(info_credito, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1.8*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.darkblue),
        ('BACKGROUND', (2, 0), (2, -1), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.white),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Cronograma de pagos
    story.append(Paragraph("CRONOGRAMA DE PAGOS", subtitle_style))
    
    # Generar fechas del cronograma
    cronograma_data = [['Cuota N°', 'Fecha de Pago', 'Valor Cuota', 'Saldo Pendiente']]
    
    fecha_base = timezone.now().date()
    saldo_pendiente = float(credito.monto_total)
    
    for i in range(credito.cantidad_cuotas):
        if credito.tipo_plazo == 'DIARIO':
            fecha_pago = fecha_base + timedelta(days=i+1)
        elif credito.tipo_plazo == 'SEMANAL':
            fecha_pago = fecha_base + timedelta(weeks=i+1)
        elif credito.tipo_plazo == 'QUINCENAL':
            fecha_pago = fecha_base + timedelta(days=(i+1)*15)
        else:  # MENSUAL
            mes = fecha_base.month + (i + 1)
            año = fecha_base.year
            while mes > 12:
                mes -= 12
                año += 1
            
            try:
                fecha_pago = fecha_base.replace(year=año, month=mes)
            except ValueError:
                from calendar import monthrange
                ultimo_dia = monthrange(año, mes)[1]
                fecha_pago = fecha_base.replace(year=año, month=mes, day=min(fecha_base.day, ultimo_dia))
        
        saldo_pendiente -= float(credito.valor_cuota)
        
        cronograma_data.append([
            f"{i+1}",
            fecha_pago.strftime('%d/%m/%Y'),
            f"${credito.valor_cuota:,.0f}",
            f"${max(0, saldo_pendiente):,.0f}"
        ])
    
    # Tabla del cronograma optimizada
    cronograma_table = Table(cronograma_data, colWidths=[0.8*inch, 1.2*inch, 1.2*inch, 1.3*inch])
    cronograma_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(cronograma_table)
    story.append(Spacer(1, 10))
    
    # Información compacta de contacto y nota final
    contacto_texto = (
        "<b>CONTACTO:</b> Tel: +57 (XXX) XXX-XXXX | Email: creditos@sistemafinanciero.com | "
        "Dirección: Calle XX #XX-XX, Ciudad<br/>"
        "<b>NOTA:</b> Cronograma válido desde el desembolso. "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    story.append(Paragraph(contacto_texto, normal_style))
    
    # Generar PDF
    doc.build(story)
    
    # Retornar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cronograma_credito_{credito.id:04d}.pdf"'
    
    return response

# Vistas adicionales para gestión de pagos
@login_required
def detalle_pago(request, pago_id):
    """Vista AJAX para obtener detalles de un pago"""
    try:
        pago = get_object_or_404(Pago, id=pago_id)
        
        return JsonResponse({
            'success': True,
            'pago': {
                'id': pago.id,
                'monto': float(pago.monto),
                'numero_cuota': pago.numero_cuota,
                'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                'observaciones': pago.observaciones or 'Sin observaciones',
                'credito': {
                    'id': pago.credito.id,
                    'monto_total': float(pago.credito.monto_total),
                    'cliente': {
                        'nombre_completo': pago.credito.cliente.nombre_completo,
                        'cedula': pago.credito.cliente.cedula,
                        'celular': pago.credito.cliente.celular,
                        'direccion': pago.credito.cliente.direccion,
                    }
                }
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def generar_recibo_pdf(request, pago_id):
    """Genera PDF del recibo de pago"""
    pago = get_object_or_404(Pago, id=pago_id)
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=15,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4
    )
    
    # Contenido del PDF
    story = []
    
    # Título principal
    story.append(Paragraph("RECIBO DE PAGO - SISTEMA DE CRÉDITOS", title_style))
    story.append(Spacer(1, 10))
    
    # Información del recibo
    info_recibo = [
        ["N° Recibo:", f"#{pago.id:05d}", "Fecha:", pago.fecha_pago.strftime('%d/%m/%Y %H:%M')],
        ["Cliente:", pago.credito.cliente.nombre_completo, "Cédula:", pago.credito.cliente.cedula],
        ["Crédito N°:", f"#{pago.credito.id:04d}", "Cuota N°:", f"{pago.numero_cuota}"],
    ]
    
    info_table = Table(info_recibo, colWidths=[1.2*inch, 2*inch, 1.2*inch, 1.8*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.darkblue),
        ('BACKGROUND', (2, 0), (2, -1), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.white),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Detalle del pago
    story.append(Paragraph("DETALLE DEL PAGO", subtitle_style))
    
    detalle_pago = [
        ["Concepto", "Monto"],
        [f"Cuota #{pago.numero_cuota} del Crédito #{pago.credito.id:04d}", f"${pago.monto:,.0f}"],
        ["", ""],
        ["TOTAL PAGADO", f"${pago.monto:,.0f}"]
    ]
    
    # Calcular información del crédito
    cuotas_pagadas = round(pago.credito.total_pagado() / pago.credito.valor_cuota)
    progreso = (cuotas_pagadas / pago.credito.cantidad_cuotas) * 100
    
    detalle_table = Table(detalle_pago, colWidths=[4*inch, 2*inch])
    detalle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
    ]))
    
    story.append(detalle_table)
    story.append(Spacer(1, 15))
    
    # Estado del crédito
    story.append(Paragraph("ESTADO DEL CRÉDITO", subtitle_style))
    
    estado_credito = [
        ["Descripción", "Valor"],
        ["Monto Total del Crédito", f"${pago.credito.monto_total:,.0f}"],
        ["Total Pagado hasta la fecha", f"${pago.credito.total_pagado():,.0f}"],
        ["Saldo Pendiente", f"${pago.credito.saldo_pendiente():,.0f}"],
        ["Cuotas Pagadas", f"{cuotas_pagadas} de {pago.credito.cantidad_cuotas}"],
        ["Progreso del Pago", f"{progreso:.1f}%"],
        ["Modalidad de Pago", pago.credito.get_tipo_plazo_display()],
        ["Valor por Cuota", f"${pago.credito.valor_cuota:,.0f}"]
    ]
    
    estado_table = Table(estado_credito, colWidths=[3*inch, 2.5*inch])
    estado_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    story.append(estado_table)
    story.append(Spacer(1, 15))
    
    # Próximo pago (si no está completo)
    if pago.credito.estado != 'PAGADO' and cuotas_pagadas < pago.credito.cantidad_cuotas:
        # Calcular próxima fecha estimada
        if pago.credito.tipo_plazo == 'DIARIO':
            proxima_fecha = pago.fecha_pago.date() + timedelta(days=1)
        elif pago.credito.tipo_plazo == 'SEMANAL':
            proxima_fecha = pago.fecha_pago.date() + timedelta(weeks=1)
        elif pago.credito.tipo_plazo == 'QUINCENAL':
            proxima_fecha = pago.fecha_pago.date() + timedelta(days=15)
        else:  # MENSUAL
            fecha_pago = pago.fecha_pago.date()
            mes = fecha_pago.month + 1
            año = fecha_pago.year
            if mes > 12:
                mes = 1
                año += 1
            try:
                proxima_fecha = fecha_pago.replace(year=año, month=mes)
            except ValueError:
                from calendar import monthrange
                ultimo_dia = monthrange(año, mes)[1]
                proxima_fecha = fecha_pago.replace(year=año, month=mes, day=min(fecha_pago.day, ultimo_dia))
        
        story.append(Paragraph("PRÓXIMO PAGO", subtitle_style))
        proximo_texto = (
            f"<b>Cuota #{cuotas_pagadas + 1}:</b> ${pago.credito.valor_cuota:,.0f}<br/>"
            f"<b>Fecha Estimada:</b> {proxima_fecha.strftime('%d/%m/%Y')}<br/>"
            f"<b>Modalidad:</b> {pago.credito.get_tipo_plazo_display()}"
        )
        story.append(Paragraph(proximo_texto, normal_style))
        story.append(Spacer(1, 15))
    
    # Observaciones
    if pago.observaciones:
        story.append(Paragraph("OBSERVACIONES", subtitle_style))
        story.append(Paragraph(pago.observaciones, normal_style))
        story.append(Spacer(1, 15))
    
    # Información de contacto y nota
    contacto_texto = (
        "<b>CONTACTO:</b> Tel: +57 (XXX) XXX-XXXX | Email: creditos@sistemafinanciero.com<br/>"
        "<b>NOTA:</b> Conserve este recibo como comprobante de pago. "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    
    story.append(Paragraph(contacto_texto, normal_style))
    
    # Generar PDF
    doc.build(story)
    
    # Retornar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_pago_{pago.id:05d}.pdf"'
    
    return response

# Vista AJAX para buscar créditos de un cliente en formulario de pago
@login_required
def buscar_creditos_cliente(request):
    """Vista AJAX para buscar créditos de un cliente por cédula"""
    cedula = request.GET.get('cedula', '').strip()
    
    if not cedula:
        return JsonResponse({
            'success': False,
            'error': 'Debe proporcionar una cédula'
        })
    
    try:
        cliente = Cliente.objects.get(cedula=cedula, activo=True)
        
        # Buscar créditos del cliente que puedan recibir pagos
        creditos = Credito.objects.filter(
            cliente=cliente,
            estado__in=['APROBADO', 'DESEMBOLSADO']
        ).exclude(estado='PAGADO')
        
        if not creditos.exists():
            return JsonResponse({
                'success': False,
                'error': f'El cliente {cliente.nombre_completo} no tiene créditos disponibles para recibir pagos'
            })
        
        # Preparar URL de la foto (si existe)
        foto_url = None
        if cliente.foto_rostro:
            try:
                foto_url = cliente.foto_rostro.url
            except ValueError:
                foto_url = None
        
        # Preparar lista de créditos
        creditos_data = []
        for credito in creditos:
            creditos_data.append({
                'id': credito.id,
                'monto_total': float(credito.monto_total),
                'saldo_pendiente': float(credito.saldo_pendiente()),
                'total_pagado': float(credito.total_pagado()),
                'estado': credito.get_estado_display(),
                'fecha_desembolso': credito.fecha_desembolso.strftime('%d/%m/%Y') if credito.fecha_desembolso else 'N/A',
                'tipo_plazo': credito.get_tipo_plazo_display(),
                'cantidad_cuotas': credito.cantidad_cuotas,
                'valor_cuota': float(credito.valor_cuota)
            })
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre_completo': cliente.nombre_completo,
                'cedula': cliente.cedula,
                'celular': cliente.celular,
                'direccion': cliente.direccion,
                'foto_url': foto_url
            },
            'creditos': creditos_data
        })
        
    except Cliente.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'No se encontró un cliente activo con cédula "{cedula}"'
        })

# ========================================
# VISTAS PARA COBRADORES Y RUTAS
# ========================================

# Vista principal del módulo de cobradores
@login_required
def cobradores(request):
    """Lista principal de cobradores"""
    cobradores = Cobrador.objects.all().order_by('nombres', 'apellidos')
    
    # Estadísticas básicas
    total_cobradores = cobradores.count()
    cobradores_activos = cobradores.filter(activo=True).count()
    
    context = {
        'cobradores': cobradores,
        'total_cobradores': total_cobradores,
        'cobradores_activos': cobradores_activos,
    }
    
    return render(request, 'cobradores/lista_cobradores.html', context)

# CRUD Cobradores
@login_required
def nuevo_cobrador(request):
    """Crear nuevo cobrador"""
    from .forms import CobradorForm
    
    if request.method == 'POST':
        form = CobradorForm(request.POST)
        if form.is_valid():
            cobrador = form.save()
            messages.success(request, f'Cobrador {cobrador.nombre_completo} creado exitosamente')
            return redirect('detalle_cobrador', cobrador_id=cobrador.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CobradorForm()
    
    return render(request, 'cobradores/nuevo_cobrador.html', {'form': form})

@login_required
def detalle_cobrador(request, cobrador_id):
    """Ver detalle completo de un cobrador"""
    cobrador = get_object_or_404(Cobrador, id=cobrador_id)
    
    # Estadísticas del cobrador
    creditos_asignados = cobrador.creditos_activos()
    monto_por_cobrar_hoy = cobrador.monto_por_cobrar_hoy()
    creditos_hoy = cobrador.creditos_por_cobrar_hoy()
    
    # Rutas asignadas
    rutas = cobrador.rutas.all()
    
    context = {
        'cobrador': cobrador,
        'creditos_asignados': creditos_asignados,
        'monto_por_cobrar_hoy': monto_por_cobrar_hoy,
        'creditos_hoy': creditos_hoy,
        'rutas': rutas,
    }
    
    return render(request, 'cobradores/detalle_cobrador.html', context)

@login_required
def editar_cobrador(request, cobrador_id):
    """Editar un cobrador existente"""
    from .forms import CobradorForm
    
    cobrador = get_object_or_404(Cobrador, id=cobrador_id)
    
    if request.method == 'POST':
        form = CobradorForm(request.POST, instance=cobrador)
        if form.is_valid():
            cobrador_actualizado = form.save()
            messages.success(request, f'Cobrador {cobrador_actualizado.nombre_completo} actualizado exitosamente')
            return redirect('detalle_cobrador', cobrador_id=cobrador.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CobradorForm(instance=cobrador)
    
    return render(request, 'cobradores/editar_cobrador.html', {
        'form': form,
        'cobrador': cobrador
    })

# Vista principal del módulo de rutas
@login_required
def rutas(request):
    """Lista principal de rutas"""
    rutas = Ruta.objects.all().order_by('nombre')
    
    # Estadísticas básicas
    total_rutas = rutas.count()
    rutas_activas = rutas.filter(activa=True).count()
    
    context = {
        'rutas': rutas,
        'total_rutas': total_rutas,
        'rutas_activas': rutas_activas,
    }
    
    return render(request, 'cobradores/lista_rutas.html', context)

# CRUD Rutas
@login_required
def nueva_ruta(request):
    """Crear nueva ruta"""
    from .forms import RutaForm
    
    if request.method == 'POST':
        form = RutaForm(request.POST)
        if form.is_valid():
            ruta = form.save()
            messages.success(request, f'Ruta "{ruta.nombre}" creada exitosamente')
            return redirect('detalle_ruta', ruta_id=ruta.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RutaForm()
    
    return render(request, 'cobradores/nueva_ruta.html', {'form': form})

@login_required
def detalle_ruta(request, ruta_id):
    """Ver detalle completo de una ruta"""
    ruta = get_object_or_404(Ruta, id=ruta_id)
    
    # Estadísticas de la ruta
    cobradores_asignados = ruta.cobradores.all()
    total_clientes = ruta.total_clientes()
    creditos_activos = ruta.total_creditos_activos()
    
    context = {
        'ruta': ruta,
        'cobradores_asignados': cobradores_asignados,
        'total_clientes': total_clientes,
        'creditos_activos': creditos_activos,
        'barrios_lista': ruta.get_barrios_lista(),
    }
    
    return render(request, 'cobradores/detalle_ruta.html', context)

@login_required
def editar_ruta(request, ruta_id):
    """Editar una ruta existente"""
    from .forms import RutaForm
    
    ruta = get_object_or_404(Ruta, id=ruta_id)
    
    if request.method == 'POST':
        form = RutaForm(request.POST, instance=ruta)
        if form.is_valid():
            ruta_actualizada = form.save()
            messages.success(request, f'Ruta "{ruta_actualizada.nombre}" actualizada exitosamente')
            return redirect('detalle_ruta', ruta_id=ruta.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RutaForm(instance=ruta)
    
    return render(request, 'cobradores/editar_ruta.html', {
        'form': form,
        'ruta': ruta
    })

# Dashboard de gestión diaria de cobros
@login_required
def gestion_diaria_cobros(request):
    """Dashboard de Control de Cobranza Diaria - Vista Administrador"""
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    
    hoy = date.today()
    
    # ===== OBTENER TODOS LOS PAGOS DEL DÍA =====
    pagos_recibidos_hoy = Pago.objects.filter(fecha_pago__date=hoy)
    monto_recaudado_hoy = pagos_recibidos_hoy.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    total_pagos_hoy = pagos_recibidos_hoy.count()
    
    # ===== LISTA DE CRÉDITOS ACTIVOS PARA GESTIÓN =====
    # Todos los créditos activos (no se limita solo a los que vencen hoy)
    creditos_activos = Credito.objects.filter(
        estado__in=['DESEMBOLSADO', 'VENCIDO']
    ).select_related('cliente', 'cobrador').order_by('-dias_mora', 'fecha_vencimiento')
    
    # Total de la cartera activa (todos los créditos pendientes)
    total_cartera_activa = sum([credito.saldo_pendiente() for credito in creditos_activos])
    
    # Créditos que requieren gestión urgente (en mora o que vencen hoy)
    creditos_urgentes = creditos_activos.filter(
        Q(fecha_vencimiento__lte=hoy, fecha_vencimiento__isnull=False) | Q(dias_mora__gt=0)
    )
    
    # Total a gestionar (créditos urgentes)
    total_a_gestionar = sum([credito.saldo_pendiente() for credito in creditos_urgentes])
    
    # Convertir a Decimal
    total_cartera_activa = Decimal(str(total_cartera_activa)) if total_cartera_activa else Decimal('0')
    total_a_gestionar = Decimal(str(total_a_gestionar)) if total_a_gestionar else Decimal('0')
    monto_recaudado_hoy = Decimal(str(monto_recaudado_hoy)) if monto_recaudado_hoy else Decimal('0')
    
    # ===== MÉTRICAS PRINCIPALES =====
    # Cobradores activos
    cobradores_activos = Cobrador.objects.filter(activo=True).count()
    
    # Créditos que han recibido pago hoy
    creditos_ids_pagados_hoy = set(pagos_recibidos_hoy.values_list('credito_id', flat=True))
    
    # Créditos urgentes sin pago hoy
    creditos_sin_pago = creditos_urgentes.exclude(id__in=creditos_ids_pagados_hoy).count()
    
    # Meta diaria (ejemplo: 10% de la cartera activa)
    meta_diaria = total_cartera_activa * Decimal('0.10')
    porcentaje_meta = float(monto_recaudado_hoy / meta_diaria * 100) if meta_diaria > 0 else 0
    
    # ===== PREPARAR DATOS DE LA TABLA PRINCIPAL (SOLO CRÉDITOS URGENTES) =====
    tareas_cobro = []
    for credito in creditos_urgentes:
        # Verificar si ya fue pagado hoy
        pago_hoy = pagos_recibidos_hoy.filter(credito=credito).first()
        
        estado_pago = 'PAGADO' if pago_hoy else 'PENDIENTE'
        monto_pagado = pago_hoy.monto if pago_hoy else 0
        hora_pago = pago_hoy.fecha_pago.time() if pago_hoy else None
        
        # Determinar prioridad
        if credito.dias_mora > 90:
            prioridad = 'CRITICA'
            color_prioridad = 'danger'
        elif credito.dias_mora > 30:
            prioridad = 'ALTA'
            color_prioridad = 'warning'
        elif credito.dias_mora > 0:
            prioridad = 'MEDIA'
            color_prioridad = 'info'
        else:
            prioridad = 'NORMAL'
            color_prioridad = 'success'
        
        tareas_cobro.append({
            'credito': credito,
            'cliente': credito.cliente,
            'cobrador': credito.cobrador,
            'monto_a_cobrar': credito.saldo_pendiente(),
            'estado_pago': estado_pago,
            'monto_pagado': monto_pagado,
            'hora_pago': hora_pago,
            'prioridad': prioridad,
            'color_prioridad': color_prioridad,
            'dias_mora': credito.dias_mora,
        })
    
    # ===== ESTADÍSTICAS POR COBRADOR =====
    resumen_cobradores = []
    total_creditos_pendientes_por_cobradores = 0
    
    for cobrador in Cobrador.objects.filter(activo=True):
        # Créditos urgentes asignados a este cobrador
        creditos_asignados = [t for t in tareas_cobro if t['cobrador'] == cobrador]
        pagos_cobrador = [t for t in creditos_asignados if t['estado_pago'] == 'PAGADO']
        pendientes_cobrador = [t for t in creditos_asignados if t['estado_pago'] == 'PENDIENTE']
        
        # Contar todos los créditos activos del cobrador (no solo urgentes)
        todos_creditos_cobrador = Credito.objects.filter(
            cobrador=cobrador, 
            estado__in=['DESEMBOLSADO', 'VENCIDO']
        ).count()
        
        monto_asignado = sum([t['monto_a_cobrar'] for t in creditos_asignados])
        monto_recaudado = sum([t['monto_pagado'] for t in pagos_cobrador])
        
        # Convertir a Decimal para evitar errores de tipo
        monto_asignado = Decimal(str(monto_asignado)) if monto_asignado else Decimal('0')
        monto_recaudado = Decimal(str(monto_recaudado)) if monto_recaudado else Decimal('0')
        
        if monto_asignado > 0 or monto_recaudado > 0 or todos_creditos_cobrador > 0:
            total_creditos_pendientes_por_cobradores += todos_creditos_cobrador
            resumen_cobradores.append({
                'cobrador': cobrador,
                'creditos_asignados': len(creditos_asignados),  # Solo urgentes
                'creditos_cobrados': len(pagos_cobrador),
                'creditos_pendientes': len(pendientes_cobrador),  # Urgentes pendientes
                'total_creditos_activos': todos_creditos_cobrador,  # Todos los créditos
                'monto_asignado': monto_asignado,
                'monto_recaudado': monto_recaudado,
                'efectividad': float(monto_recaudado / monto_asignado * 100) if monto_asignado > 0 else 0,
            })
    
    # ===== COMPARACIÓN CON DÍA ANTERIOR =====
    ayer = hoy - timedelta(days=1)
    monto_ayer = Pago.objects.filter(fecha_pago__date=ayer).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    monto_ayer = Decimal(str(monto_ayer)) if monto_ayer else Decimal('0')
    variacion_diaria = float((monto_recaudado_hoy - monto_ayer) / monto_ayer * 100) if monto_ayer > 0 else 0
    
    context = {
        'fecha_hoy': hoy,
        # Métricas principales
        'total_a_cobrar_hoy': total_a_gestionar,  # Ahora muestra solo créditos urgentes
        'total_cartera_activa': total_cartera_activa,  # Nueva métrica
        'monto_recaudado_hoy': monto_recaudado_hoy,
        'cobradores_activos': cobradores_activos,
        'clientes_pendientes': creditos_sin_pago,
        'total_pagos_hoy': total_pagos_hoy,
        'meta_diaria': meta_diaria,
        'porcentaje_meta': porcentaje_meta,
        # Tabla principal
        'tareas_cobro': tareas_cobro,
        'total_tareas': len(tareas_cobro),
        # Resumen por cobrador
        'resumen_cobradores': resumen_cobradores,
        'total_creditos_por_cobradores': total_creditos_pendientes_por_cobradores,
        # Comparaciones
        'monto_ayer': monto_ayer,
        'variacion_diaria': variacion_diaria,
    }
    
    return render(request, 'cobradores/gestion_diaria.html', context)

# Reportes de recaudación por cobrador
# ========================================
# VISTAS PARA GESTIÓN DE CARTERA
# ========================================

@login_required
def gestion_cartera(request):
    """Vista principal de gestión de cartera - Calcula datos reales"""
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Avg
    from decimal import Decimal
    
    hoy = date.today()
    
    # ===== CALCULAR MÉTRICAS REALES DESDE LA BASE DE DATOS =====
    
    # Todos los créditos activos
    creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO'])
    
    # Cartera total (suma de saldos pendientes)
    cartera_total = sum([credito.saldo_pendiente() for credito in creditos_activos]) or Decimal('0')
    cartera_total = Decimal(str(cartera_total))
    
    # Créditos por estado
    creditos_al_dia = creditos_activos.filter(dias_mora=0)
    creditos_en_mora = creditos_activos.filter(dias_mora__gt=0)
    
    # Cartera al día y vencida
    cartera_al_dia_monto = sum([credito.saldo_pendiente() for credito in creditos_al_dia]) or Decimal('0')
    cartera_vencida_monto = sum([credito.saldo_pendiente() for credito in creditos_en_mora]) or Decimal('0')
    
    cartera_al_dia_monto = Decimal(str(cartera_al_dia_monto))
    cartera_vencida_monto = Decimal(str(cartera_vencida_monto))
    
    # Porcentaje de cartera vencida
    porcentaje_cartera_vencida = float(cartera_vencida_monto / cartera_total * 100) if cartera_total > 0 else 0
    
    # Créditos por rango de mora
    creditos_mora_temprana = creditos_activos.filter(dias_mora__range=(1, 30))
    creditos_mora_alta = creditos_activos.filter(dias_mora__range=(31, 90))
    creditos_mora_critica = creditos_activos.filter(dias_mora__gt=90)
    
    # Pagos del día
    pagos_del_dia = Pago.objects.filter(fecha_pago__date=hoy)
    monto_pagos_del_dia = pagos_del_dia.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Meta diaria (ejemplo: 5% de la cartera total)
    meta_cobranza_diaria = cartera_total * Decimal('0.05')
    porcentaje_cumplimiento_meta = float(monto_pagos_del_dia / meta_cobranza_diaria * 100) if meta_cobranza_diaria > 0 else 0
    
    # Días de mora promedio
    dias_mora_promedio = creditos_en_mora.aggregate(promedio=Avg('dias_mora'))['promedio'] or 0
    
    # Crear objeto con datos reales
    analisis_hoy = type('AnalisisBasico', (), {
        'cartera_total': float(cartera_total),
        'cartera_al_dia': float(cartera_al_dia_monto),
        'cartera_vencida': float(cartera_vencida_monto),
        'porcentaje_cartera_vencida': porcentaje_cartera_vencida,
        'creditos_al_dia': creditos_al_dia.count(),
        'creditos_mora_temprana': creditos_mora_temprana.count(),
        'creditos_mora_alta': creditos_mora_alta.count(),
        'creditos_mora_critica': creditos_mora_critica.count(),
        'pagos_del_dia': float(monto_pagos_del_dia),
        'meta_cobranza_diaria': float(meta_cobranza_diaria),
        'porcentaje_cumplimiento_meta': porcentaje_cumplimiento_meta,
        'dias_mora_promedio': float(dias_mora_promedio or 0),
    })()
    
    # Usar las variables ya calculadas arriba (no recalcular)
    
    # Créditos más críticos (por días de mora)
    creditos_criticos = Credito.objects.filter(
        estado__in=['DESEMBOLSADO', 'VENCIDO'],
        dias_mora__gt=0
    ).order_by('-dias_mora')[:10]
    
    # Evolución de cartera - lista vacía por ahora para evitar errores
    analisis_historico = []
    
    context = {
        'analisis_hoy': analisis_hoy,
        'creditos_al_dia': creditos_al_dia,
        'creditos_mora_temp': creditos_mora_temprana,
        'creditos_mora_alta': creditos_mora_alta,
        'creditos_mora_critica': creditos_mora_critica,
        'creditos_criticos': creditos_criticos,
        'analisis_historico': analisis_historico,
    }
    
    return render(request, 'cartera/gestion_cartera.html', context)

@login_required
def cartera_vencida(request):
    """Vista de cartera vencida con filtros"""
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    # Filtros
    estado_mora = request.GET.get('estado_mora', '')
    dias_mora_min = request.GET.get('dias_mora_min', '')
    cobrador_id = request.GET.get('cobrador_id', '')
    
    # Base query
    creditos_vencidos_list = Credito.objects.filter(
        estado__in=['DESEMBOLSADO', 'VENCIDO'],
        dias_mora__gt=0
    ).select_related('cliente', 'cobrador')
    
    # Aplicar filtros
    if estado_mora:
        creditos_vencidos_list = creditos_vencidos_list.filter(estado_mora=estado_mora)
    
    if dias_mora_min:
        try:
            dias_min = int(dias_mora_min)
            creditos_vencidos_list = creditos_vencidos_list.filter(dias_mora__gte=dias_min)
        except ValueError:
            pass
    
    if cobrador_id:
        try:
            cobrador_id = int(cobrador_id)
            creditos_vencidos_list = creditos_vencidos_list.filter(cobrador_id=cobrador_id)
        except ValueError:
            pass
    
    # Ordenar por días de mora descendente
    creditos_vencidos_list = creditos_vencidos_list.order_by('-dias_mora')
    
    # Paginación: 20 créditos por página
    paginator = Paginator(creditos_vencidos_list, 20)
    page_number = request.GET.get('page')
    creditos_vencidos = paginator.get_page(page_number)
    
    # Para los filtros en el template
    cobradores = Cobrador.objects.filter(activo=True)
    
    context = {
        'creditos_vencidos': creditos_vencidos,
        'cobradores': cobradores,
        'estado_mora': estado_mora,
        'dias_mora_min': dias_mora_min,
        'cobrador_id': cobrador_id,
    }
    
    return render(request, 'cartera/cartera_vencida.html', context)

@login_required
def actualizar_cartera(request):
    """Actualiza el estado de cartera de todos los créditos"""
    if request.method == 'POST':
        # Actualizar todos los créditos activos
        creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO'])
        cantidad_actualizados = 0
        
        for credito in creditos_activos:
            credito.actualizar_estado_cartera()
            cantidad_actualizados += 1
        
        # Generar nuevo análisis
        from .models import CarteraAnalisis
        CarteraAnalisis.generar_analisis_diario()
        
        messages.success(request, f'Se actualizó el estado de cartera de {cantidad_actualizados} créditos.')
    
    return redirect('gestion_cartera')

@login_required
def exportar_cartera_excel(request):
    """Exporta la cartera vencida a un archivo Excel"""
    from django.http import HttpResponse
    from django.db.models import Q
    import pandas as pd
    from datetime import datetime
    import io
    
    # Aplicar los mismos filtros que en cartera_vencida
    estado_mora = request.GET.get('estado_mora', '')
    dias_mora_min = request.GET.get('dias_mora_min', '')
    cobrador_id = request.GET.get('cobrador_id', '')
    
    # Base query
    creditos_vencidos = Credito.objects.filter(
        estado__in=['DESEMBOLSADO', 'VENCIDO'],
        dias_mora__gt=0
    ).select_related('cliente', 'cobrador')
    
    # Aplicar filtros
    if estado_mora:
        creditos_vencidos = creditos_vencidos.filter(estado_mora=estado_mora)
    
    if dias_mora_min:
        try:
            dias_min = int(dias_mora_min)
            creditos_vencidos = creditos_vencidos.filter(dias_mora__gte=dias_min)
        except ValueError:
            pass
    
    if cobrador_id:
        try:
            cobrador_id = int(cobrador_id)
            creditos_vencidos = creditos_vencidos.filter(cobrador_id=cobrador_id)
        except ValueError:
            pass
    
    # Ordenar por días de mora descendente
    creditos_vencidos = creditos_vencidos.order_by('-dias_mora')
    
    # Preparar datos para Excel
    data = []
    for credito in creditos_vencidos:
        data.append({
            'ID Crédito': credito.id,
            'Cliente': credito.cliente.nombre_completo,
            'Cédula': credito.cliente.cedula,
            'Teléfono': credito.cliente.celular,
            'Dirección': credito.cliente.direccion,
            'Barrio': credito.cliente.barrio,
            'Monto Original': float(credito.monto),
            'Monto Total': float(credito.monto_total) if credito.monto_total else float(credito.monto),
            'Saldo Pendiente': float(credito.saldo_pendiente()),
            'Total Pagado': float(credito.total_pagado()),
            'Días Mora': credito.dias_mora,
            'Estado Mora': credito.get_estado_mora_display(),
            'Interés Moratorio': float(credito.interes_moratorio),
            'Tasa Mora (%)': float(credito.tasa_mora),
            'Tipo Plazo': credito.get_tipo_plazo_display(),
            'Cantidad Cuotas': credito.cantidad_cuotas,
            'Cobrador': credito.cobrador.nombre_completo if credito.cobrador else 'Sin asignar',
            'Teléfono Cobrador': credito.cobrador.celular if credito.cobrador else '',
            'Fecha Desembolso': credito.fecha_desembolso.strftime('%d/%m/%Y') if credito.fecha_desembolso else '',
            'Estado Crédito': credito.get_estado_display()
        })
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    # Crear archivo Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja principal con datos
        df.to_excel(writer, sheet_name='Cartera Vencida', index=False)
        
        # Obtener la hoja para formatear
        worksheet = writer.sheets['Cartera Vencida']
        
        # Ajustar ancho de columnas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Agregar hoja de resúmenes
        if data:
            resumen_data = []
            total_creditos = len(data)
            total_saldo = sum([item['Saldo Pendiente'] for item in data])
            total_intereses = sum([item['Interés Moratorio'] for item in data])
            mora_promedio = sum([item['Días Mora'] for item in data]) / total_creditos if total_creditos > 0 else 0
            
            resumen_data.append(['RESUMEN DE CARTERA VENCIDA', ''])
            resumen_data.append(['Fecha del Reporte', datetime.now().strftime('%d/%m/%Y %H:%M')])
            resumen_data.append(['', ''])
            resumen_data.append(['Total Créditos Vencidos', total_creditos])
            resumen_data.append(['Saldo Total Vencido', f'${total_saldo:,.2f}'])
            resumen_data.append(['Intereses Moratorios', f'${total_intereses:,.2f}'])
            resumen_data.append(['Días Mora Promedio', f'{mora_promedio:.1f}'])
            resumen_data.append(['', ''])
            
            # Por estado de mora
            estados = {}
            for item in data:
                estado = item['Estado Mora']
                if estado not in estados:
                    estados[estado] = 0
                estados[estado] += 1
            
            resumen_data.append(['DISTRIBUCIÓN POR ESTADO DE MORA', ''])
            for estado, cantidad in estados.items():
                resumen_data.append([estado, cantidad])
            
            # Crear hoja de resumen
            df_resumen = pd.DataFrame(resumen_data, columns=['Concepto', 'Valor'])
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    output.seek(0)
    
    # Preparar respuesta
    filename = f'cartera_vencida_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def kpis_cobradores(request):
    """Vista detallada de KPIs por cobrador"""
    from datetime import date, timedelta
    from django.db.models import Q, Sum, Count, Avg, Max, Min
    from .models import TareaCobro, CarteraAnalisis
    
    # Parámetros de filtrado
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cobrador_id = request.GET.get('cobrador_id')
    
    # Fechas por defecto (últimos 30 días)
    if not fecha_desde:
        fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    # Convertir a objetos date
    from datetime import datetime
    fecha_inicio = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    
    # Obtener todos los cobradores activos
    cobradores_query = Cobrador.objects.filter(activo=True)
    if cobrador_id:
        cobradores_query = cobradores_query.filter(id=cobrador_id)
    cobradores = cobradores_query.order_by('nombres', 'apellidos')
    
    # Calcular KPIs por cobrador
    datos_cobradores = []
    
    for cobrador in cobradores:
        # KPIs de Recaudación
        pagos_cobrador = Pago.objects.filter(
            credito__cobrador=cobrador,
            fecha_pago__date__gte=fecha_inicio,
            fecha_pago__date__lte=fecha_fin
        )
        
        total_recaudado = pagos_cobrador.aggregate(Sum('monto'))['monto__sum'] or 0
        cantidad_pagos = pagos_cobrador.count()
        promedio_pago = total_recaudado / cantidad_pagos if cantidad_pagos > 0 else 0
        
        # KPIs de Tareas de Cobro
        tareas_cobrador = TareaCobro.objects.filter(
            cobrador=cobrador,
            fecha_asignacion__gte=fecha_inicio,
            fecha_asignacion__lte=fecha_fin
        )
        
        total_tareas = tareas_cobrador.count()
        tareas_cobradas = tareas_cobrador.filter(estado='COBRADO').count()
        tareas_pendientes = tareas_cobrador.filter(estado='PENDIENTE').count()
        tareas_no_encontrado = tareas_cobrador.filter(estado='NO_ENCONTRADO').count()
        tareas_reprogramadas = tareas_cobrador.filter(estado='REPROGRAMADO').count()
        
        # Efectividad de cobro
        efectividad_cobro = (tareas_cobradas / total_tareas * 100) if total_tareas > 0 else 0
        
        # KPIs de Cartera Asignada
        creditos_asignados = Credito.objects.filter(cobrador=cobrador)
        cartera_total_cobrador = creditos_asignados.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
        creditos_vencidos_cobrador = creditos_asignados.filter(dias_mora__gt=0).count()
        creditos_al_dia_cobrador = creditos_asignados.filter(dias_mora=0).count()
        
        # Mora promedio de la cartera del cobrador
        mora_promedio = creditos_asignados.filter(dias_mora__gt=0).aggregate(
            Avg('dias_mora')
        )['dias_mora__avg'] or 0
        
        # Meta diaria y cumplimiento
        meta_periodo = cobrador.meta_diaria * dias_periodo if cobrador.meta_diaria else 0
        cumplimiento_meta = (total_recaudado / meta_periodo * 100) if meta_periodo > 0 else 0
        
        # Productividad diaria
        productividad_diaria = total_recaudado / dias_periodo if dias_periodo > 0 else 0
        tareas_diaria_promedio = total_tareas / dias_periodo if dias_periodo > 0 else 0
        
        # Tasa de contacto efectivo
        tareas_con_contacto = tareas_cobrador.exclude(estado='NO_ENCONTRADO').count()
        tasa_contacto = (tareas_con_contacto / total_tareas * 100) if total_tareas > 0 else 0
        
        # Calificación general (score)
        score = 0
        if efectividad_cobro >= 80: score += 25
        elif efectividad_cobro >= 60: score += 20
        elif efectividad_cobro >= 40: score += 15
        elif efectividad_cobro >= 20: score += 10
        
        if cumplimiento_meta >= 100: score += 25
        elif cumplimiento_meta >= 80: score += 20
        elif cumplimiento_meta >= 60: score += 15
        elif cumplimiento_meta >= 40: score += 10
        
        if tasa_contacto >= 85: score += 25
        elif tasa_contacto >= 70: score += 20
        elif tasa_contacto >= 55: score += 15
        elif tasa_contacto >= 40: score += 10
        
        if mora_promedio <= 15: score += 25
        elif mora_promedio <= 30: score += 20
        elif mora_promedio <= 45: score += 15
        elif mora_promedio <= 60: score += 10
        
        # Determinar nivel de rendimiento
        if score >= 90:
            nivel_rendimiento = 'EXCELENTE'
            color_rendimiento = 'success'
        elif score >= 70:
            nivel_rendimiento = 'BUENO'
            color_rendimiento = 'primary'
        elif score >= 50:
            nivel_rendimiento = 'REGULAR'
            color_rendimiento = 'warning'
        else:
            nivel_rendimiento = 'NECESITA MEJORA'
            color_rendimiento = 'danger'
        
        datos_cobradores.append({
            'cobrador': cobrador,
            'total_recaudado': total_recaudado,
            'cantidad_pagos': cantidad_pagos,
            'promedio_pago': promedio_pago,
            'total_tareas': total_tareas,
            'tareas_cobradas': tareas_cobradas,
            'tareas_pendientes': tareas_pendientes,
            'tareas_no_encontrado': tareas_no_encontrado,
            'tareas_reprogramadas': tareas_reprogramadas,
            'efectividad_cobro': efectividad_cobro,
            'cartera_total_cobrador': cartera_total_cobrador,
            'creditos_vencidos_cobrador': creditos_vencidos_cobrador,
            'creditos_al_dia_cobrador': creditos_al_dia_cobrador,
            'mora_promedio': mora_promedio,
            'meta_periodo': meta_periodo,
            'cumplimiento_meta': cumplimiento_meta,
            'productividad_diaria': productividad_diaria,
            'tareas_diaria_promedio': tareas_diaria_promedio,
            'tasa_contacto': tasa_contacto,
            'score': score,
            'nivel_rendimiento': nivel_rendimiento,
            'color_rendimiento': color_rendimiento,
        })
    
    # Ordenar por score descendente
    datos_cobradores.sort(key=lambda x: x['score'], reverse=True)
    
    # Calcular promedios generales
    if datos_cobradores:
        promedio_efectividad = sum([d['efectividad_cobro'] for d in datos_cobradores]) / len(datos_cobradores)
        promedio_cumplimiento = sum([d['cumplimiento_meta'] for d in datos_cobradores]) / len(datos_cobradores)
        promedio_contacto = sum([d['tasa_contacto'] for d in datos_cobradores]) / len(datos_cobradores)
        total_recaudado_general = sum([d['total_recaudado'] for d in datos_cobradores])
        total_tareas_general = sum([d['total_tareas'] for d in datos_cobradores])
    else:
        promedio_efectividad = promedio_cumplimiento = promedio_contacto = 0
        total_recaudado_general = total_tareas_general = 0
    
    context = {
        'datos_cobradores': datos_cobradores,
        'cobradores_todos': Cobrador.objects.filter(activo=True),
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cobrador_id': int(cobrador_id) if cobrador_id else None,
        'dias_periodo': dias_periodo,
        'promedio_efectividad': promedio_efectividad,
        'promedio_cumplimiento': promedio_cumplimiento,
        'promedio_contacto': promedio_contacto,
        'total_recaudado_general': total_recaudado_general,
        'total_tareas_general': total_tareas_general,
    }
    
    return render(request, 'cartera/kpis_cobradores.html', context)

# ========================================
# SISTEMA DE TAREAS DE COBRO DIARIAS
# ========================================

@login_required
def acceso_cobrador(request):
    """Vista de acceso optimizada para cobradores móviles"""
    return render(request, 'tareas/acceso_cobrador.html')

@login_required
def agenda_cobrador(request, cobrador_id=None):
    """Vista de agenda diaria para cobradores"""
    from datetime import date, timedelta
    from django.db.models import Count, Sum
    from .models import TareaCobro
    
    # Si no se especifica cobrador, intentar detectar por usuario logueado
    if not cobrador_id:
        try:
            cobrador = Cobrador.objects.get(usuario=request.user)
            cobrador_id = cobrador.id
        except Cobrador.DoesNotExist:
            # Si el usuario no es cobrador, mostrar selector
            cobradores = Cobrador.objects.filter(activo=True)
            return render(request, 'tareas/selector_cobrador.html', {
                'cobradores': cobradores
            })
    else:
        cobrador = get_object_or_404(Cobrador, id=cobrador_id, activo=True)
    
    # Fecha a consultar (por defecto hoy)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()
    
    # Obtener tareas del cobrador para la fecha
    tareas = TareaCobro.objects.filter(
        cobrador=cobrador,
        fecha_asignacion=fecha
    ).select_related(
        'cuota__credito__cliente'
    ).order_by('orden_visita', 'prioridad')
    
    # Estadísticas del día
    total_tareas = tareas.count()
    tareas_completadas = tareas.filter(estado='COBRADO').count()
    monto_total_cobrar = sum(tarea.monto_a_cobrar for tarea in tareas)
    monto_cobrado = tareas.filter(estado='COBRADO').aggregate(
        total=Sum('monto_cobrado')
    )['total'] or 0
    
    porcentaje_completado = (tareas_completadas / total_tareas * 100) if total_tareas > 0 else 0
    
    # Agrupar tareas por estado para estadísticas
    tareas_por_estado = tareas.values('estado').annotate(cantidad=Count('id'))
    estadisticas_estado = {item['estado']: item['cantidad'] for item in tareas_por_estado}
    
    context = {
        'cobrador': cobrador,
        'fecha': fecha,
        'tareas': tareas,
        'total_tareas': total_tareas,
        'tareas_completadas': tareas_completadas,
        'monto_total_cobrar': monto_total_cobrar,
        'monto_cobrado': monto_cobrado,
        'porcentaje_completado': porcentaje_completado,
        'estadisticas_estado': estadisticas_estado,
        'puede_editar': request.user.is_staff or (hasattr(request.user, 'cobrador') and request.user.cobrador == cobrador)
    }
    
    return render(request, 'tareas/agenda_cobrador.html', context)

@login_required
def procesar_cobro_completo(request, tarea_id):
    """Vista para procesar cobro completo - MISMA LÓGICA que nuevo_pago"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        tarea = get_object_or_404(TareaCobro, id=tarea_id)
        
        # Verificar permisos
        if not (request.user.is_staff or (hasattr(request.user, 'cobrador') and request.user.cobrador == tarea.cobrador)):
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Obtener datos del formulario
        monto_cobrado = request.POST.get('monto_recibido')
        observaciones = request.POST.get('observaciones', '')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        
        if not monto_cobrado:
            return JsonResponse({'success': False, 'error': 'Debe especificar el monto cobrado'})
        
        try:
            monto = float(monto_cobrado)
            if monto <= 0:
                return JsonResponse({'success': False, 'error': 'El monto debe ser mayor que cero'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Monto inválido'})
        
        from decimal import Decimal
        
        # 🎯 USAR EXACTAMENTE LA MISMA LÓGICA QUE nuevo_pago - CREAR PAGO
        pago = Pago.objects.create(
            credito=tarea.credito,
            cuota=tarea.cuota,
            monto=Decimal(str(monto)),
            numero_cuota=tarea.cuota.numero_cuota,
            observaciones=f"📱 Cobro por {tarea.cobrador.nombre_completo}\n{observaciones}".strip()
        )
        
        credito = pago.credito
        
        # 🎯 ACTUALIZAR ESTADO DEL CRÉDITO - MISMA LÓGICA QUE nuevo_pago
        if credito.esta_al_dia():
            credito.estado = 'PAGADO'
            credito.save()
        
        # Actualizar tarea como cobrada
        tarea.estado = 'COBRADO'
        tarea.fecha_visita = timezone.now()
        tarea.monto_cobrado = Decimal(str(monto))
        tarea.observaciones = observaciones
        if latitud:
            tarea.latitud = float(latitud)
        if longitud:
            tarea.longitud = float(longitud)
        tarea.save()
        
        # Actualizar cuota
        tarea.cuota.monto_pagado += Decimal(str(monto))
        if tarea.cuota.monto_pagado >= tarea.cuota.monto_cuota:
            tarea.cuota.estado = 'PAGADA'
            tarea.cuota.fecha_pago = timezone.now().date()
        else:
            tarea.cuota.estado = 'PARCIAL'
        tarea.cuota.save()
        
        # 🎯 REDIRIGIR AL MISMO FLUJO QUE nuevo_pago
        return JsonResponse({
            'success': True,
            'mensaje': 'Pago registrado exitosamente',
            'pago_id': pago.id,
            'redirect_url': f'/confirmacion-pago/{pago.id}/'
        })
        
    except Exception as e:
        print(f"ERROR EN PROCESAR_COBRO_COMPLETO: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })

@login_required
def actualizar_tarea(request, tarea_id):
    """Vista AJAX para actualizar estado de una tarea"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        tarea = get_object_or_404(TareaCobro, id=tarea_id)
        
        # Verificar permisos
        if not (request.user.is_staff or (hasattr(request.user, 'cobrador') and request.user.cobrador == tarea.cobrador)):
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        nuevo_estado = request.POST.get('estado')
        observaciones = request.POST.get('observaciones', '')
        monto_cobrado = request.POST.get('monto_cobrado')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        fecha_reprogramacion = request.POST.get('fecha_reprogramacion')
        
        if nuevo_estado == 'COBRADO':
            if not monto_cobrado:
                return JsonResponse({'success': False, 'error': 'Debe especificar el monto cobrado'})
            
            try:
                monto = float(monto_cobrado)
                if monto <= 0:
                    return JsonResponse({'success': False, 'error': 'El monto debe ser mayor que cero'})
                
                lat = float(latitud) if latitud else None
                lng = float(longitud) if longitud else None
                
                # 🎆 MAGIA: Marcar tarea Y crear pago automáticamente
                pago_creado = tarea.marcar_como_cobrado(monto, observaciones, lat, lng)
                
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Monto inválido'})
        else:
            fecha_reprog = None
            if fecha_reprogramacion:
                try:
                    fecha_reprog = datetime.strptime(fecha_reprogramacion, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            tarea.cambiar_estado(nuevo_estado, observaciones, fecha_reprog)
        
        # Preparar respuesta base
        response_data = {
            'success': True,
            'tarea': {
                'id': tarea.id,
                'estado': tarea.estado,
                'estado_display': tarea.get_estado_display(),
                'color_estado': tarea.color_estado,
                'monto_cobrado': float(tarea.monto_cobrado) if tarea.monto_cobrado else 0,
                'observaciones': tarea.observaciones,
                'fecha_visita': tarea.fecha_visita.strftime('%H:%M') if tarea.fecha_visita else None
            }
        }
        
        # Si se creó un pago, incluir información del pago
        if nuevo_estado == 'COBRADO' and 'pago_creado' in locals():
            response_data['pago'] = {
                'id': pago_creado.id,
                'monto': float(pago_creado.monto),
                'fecha': pago_creado.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                'cliente': tarea.credito.cliente.nombre_completo,
                'cuota': tarea.cuota.numero_cuota,
                'mensaje': f'✅ Pago de ${pago_creado.monto:,.0f} registrado exitosamente'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def panel_supervisor(request):
    """Panel de supervisor para ver progreso de todos los cobradores"""
    from datetime import date, timedelta
    from django.db.models import Count, Sum, Avg
    from .models import TareaCobro
    
    # Fecha a consultar (por defecto hoy)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()
    
    # Obtener todos los cobradores activos
    cobradores = Cobrador.objects.filter(activo=True)
    
    # Datos por cobrador
    datos_cobradores = []
    total_general_tareas = 0
    total_general_cobradas = 0
    total_general_monto = 0
    
    for cobrador in cobradores:
        tareas = TareaCobro.objects.filter(
            cobrador=cobrador,
            fecha_asignacion=fecha
        ).select_related('cuota__credito__cliente')
        
        total_tareas = tareas.count()
        tareas_cobradas = tareas.filter(estado='COBRADO').count()
        monto_cobrado = tareas.filter(estado='COBRADO').aggregate(
            total=Sum('monto_cobrado')
        )['total'] or 0
        
        porcentaje = (tareas_cobradas / total_tareas * 100) if total_tareas > 0 else 0
        
        # Últimas tareas actualizadas
        ultimas_tareas = tareas.exclude(estado='PENDIENTE').order_by('-fecha_visita')[:3]
        
        datos_cobradores.append({
            'cobrador': cobrador,
            'total_tareas': total_tareas,
            'tareas_cobradas': tareas_cobradas,
            'tareas_pendientes': total_tareas - tareas_cobradas,
            'monto_cobrado': monto_cobrado,
            'porcentaje': porcentaje,
            'ultimas_tareas': ultimas_tareas,
            'rutas': cobrador.rutas.all()
        })
        
        total_general_tareas += total_tareas
        total_general_cobradas += tareas_cobradas
        total_general_monto += monto_cobrado
    
    # Ordenar por porcentaje de completado (mayor a menor)
    datos_cobradores.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    # Estadísticas generales
    porcentaje_general = (total_general_cobradas / total_general_tareas * 100) if total_general_tareas > 0 else 0
    
    # Tareas por estado (todas)
    todas_tareas = TareaCobro.objects.filter(fecha_asignacion=fecha)
    estadisticas_estado = todas_tareas.values('estado').annotate(cantidad=Count('id'))
    
    context = {
        'fecha': fecha,
        'datos_cobradores': datos_cobradores,
        'total_general_tareas': total_general_tareas,
        'total_general_cobradas': total_general_cobradas,
        'total_general_monto': total_general_monto,
        'porcentaje_general': porcentaje_general,
        'estadisticas_estado': {item['estado']: item['cantidad'] for item in estadisticas_estado}
    }
    
    return render(request, 'tareas/panel_supervisor.html', context)

@login_required
def generar_tareas_diarias(request):
    """Vista para generar tareas diarias manualmente"""
    if request.method == 'POST':
        fecha_str = request.POST.get('fecha')
        try:
            if fecha_str:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            else:
                fecha = date.today()
            
            from .models import TareaCobro
            tareas_creadas = TareaCobro.generar_tareas_diarias(fecha)
            
            messages.success(request, f'Se generaron {tareas_creadas} tareas para {fecha.strftime("%d/%m/%Y")}')
            
        except Exception as e:
            messages.error(request, f'Error al generar tareas: {str(e)}')
    
    return redirect('panel_supervisor')

# ========================================
# REPORTES DE RECAUDACIÓN
# ========================================

@login_required
def recaudacion_cobradores(request):
    """Vista para mostrar reportes de recaudación por cobrador"""
    from datetime import date, timedelta
    from django.db.models import Q, Sum, Count, Avg
    
    # Parámetros de filtrado
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cobrador_id = request.GET.get('cobrador_id')
    
    # Fechas por defecto (día actual)
    if not fecha_desde:
        fecha_desde = date.today().strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    # Filtrar pagos por fechas
    filtros_pagos = Q(fecha_pago__date__gte=fecha_desde) & Q(fecha_pago__date__lte=fecha_hasta)
    
    # Si se especifica un cobrador, filtrar solo ese
    if cobrador_id:
        filtros_pagos &= Q(credito__cobrador_id=cobrador_id)
    
    # Obtener todos los cobradores activos
    cobradores = Cobrador.objects.filter(activo=True).order_by('nombres', 'apellidos')
    
    # Datos de recaudación por cobrador
    datos_recaudacion = []
    total_general_recaudado = 0
    total_general_pagos = 0
    
    for cobrador in cobradores:
        # Pagos del cobrador en el período
        pagos_cobrador = Pago.objects.filter(
            filtros_pagos & Q(credito__cobrador=cobrador)
        )
        
        # Estadísticas del cobrador
        total_recaudado = pagos_cobrador.aggregate(Sum('monto'))['monto__sum'] or 0
        cantidad_pagos = pagos_cobrador.count()
        promedio_pago = total_recaudado / cantidad_pagos if cantidad_pagos > 0 else 0
        
        # Créditos únicos gestionados
        creditos_gestionados = pagos_cobrador.values('credito').distinct().count()
        
        # Cumplimiento de meta (si tiene meta diaria)
        cumplimiento_meta = 0
        if cobrador.meta_diaria and cobrador.meta_diaria > 0:
            # Calcular días en el período
            from datetime import datetime
            fecha_inicio = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            dias_periodo = (fecha_fin - fecha_inicio).days + 1
            meta_periodo = cobrador.meta_diaria * dias_periodo
            cumplimiento_meta = (total_recaudado / meta_periodo * 100) if meta_periodo > 0 else 0
        
        # Solo incluir cobradores que tienen actividad o siempre mostrar todos
        if total_recaudado > 0 or not cobrador_id:  # Mostrar todos si no hay filtro específico
            datos_recaudacion.append({
                'cobrador': cobrador,
                'total_recaudado': total_recaudado,
                'cantidad_pagos': cantidad_pagos,
                'promedio_pago': promedio_pago,
                'creditos_gestionados': creditos_gestionados,
                'cumplimiento_meta': cumplimiento_meta,
                'pagos': pagos_cobrador.order_by('-fecha_pago')[:5],  # Últimos 5 pagos
            })
        
        total_general_recaudado += total_recaudado
        total_general_pagos += cantidad_pagos
    
    # Ordenar por total recaudado (mayor a menor)
    datos_recaudacion.sort(key=lambda x: x['total_recaudado'], reverse=True)
    
    # Estadísticas generales
    promedio_general = total_general_recaudado / total_general_pagos if total_general_pagos > 0 else 0
    
    # Top performers
    top_recaudadores = datos_recaudacion[:3]  # Top 3
    
    context = {
        'datos_recaudacion': datos_recaudacion,
        'cobradores': cobradores,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cobrador_id': int(cobrador_id) if cobrador_id else None,
        'total_general_recaudado': total_general_recaudado,
        'total_general_pagos': total_general_pagos,
        'promedio_general': promedio_general,
        'top_recaudadores': top_recaudadores,
    }
    
    return render(request, 'cobradores/recaudacion_cobradores.html', context)

# Vista AJAX para obtener detalles de pagos por cobrador
@login_required
def detalles_pagos_cobrador(request, cobrador_id):
    """Vista AJAX que devuelve detalles completos de pagos de un cobrador"""
    try:
        cobrador = get_object_or_404(Cobrador, id=cobrador_id)
        
        # Parámetros de filtrado
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        buscar = request.GET.get('buscar', '').strip()
        
        # Fechas por defecto (día actual)
        if not fecha_desde:
            fecha_desde = date.today().strftime('%Y-%m-%d')
        if not fecha_hasta:
            fecha_hasta = date.today().strftime('%Y-%m-%d')
        
        # Filtrar pagos del cobrador
        pagos = Pago.objects.filter(
            credito__cobrador=cobrador,
            fecha_pago__date__gte=fecha_desde,
            fecha_pago__date__lte=fecha_hasta
        ).select_related(
            'credito__cliente'
        ).order_by('-fecha_pago')
        
        # Filtro de búsqueda por nombre de cliente
        if buscar:
            pagos = pagos.filter(
                Q(credito__cliente__nombres__icontains=buscar) |
                Q(credito__cliente__apellidos__icontains=buscar) |
                Q(credito__cliente__cedula__icontains=buscar)
            )
        
        # Estadísticas del período
        total_recaudado = pagos.aggregate(Sum('monto'))['monto__sum'] or 0
        cantidad_pagos = pagos.count()
        promedio_pago = total_recaudado / cantidad_pagos if cantidad_pagos > 0 else 0
        creditos_unicos = pagos.values('credito').distinct().count()
        
        # Convertir pagos a lista de diccionarios
        pagos_data = []
        for pago in pagos[:50]:  # Limitar a 50 para rendimiento
            pagos_data.append({
                'id': pago.id,
                'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y %H:%M'),
                'fecha_pago_corta': pago.fecha_pago.strftime('%d/%m/%Y'),
                'hora_pago': pago.fecha_pago.strftime('%H:%M'),
                'monto': float(pago.monto),
                'numero_cuota': pago.numero_cuota,
                'observaciones': pago.observaciones or '',
                'cliente': {
                    'id': pago.credito.cliente.id,
                    'nombre_completo': pago.credito.cliente.nombre_completo,
                    'nombres': pago.credito.cliente.nombres,
                    'apellidos': pago.credito.cliente.apellidos,
                    'cedula': pago.credito.cliente.cedula,
                    'celular': pago.credito.cliente.celular,
                    'direccion': pago.credito.cliente.direccion,
                    'barrio': pago.credito.cliente.barrio,
                },
                'credito': {
                    'id': pago.credito.id,
                    'monto_total': float(pago.credito.monto),
                    'estado': pago.credito.get_estado_display(),
                    'tasa_interes': float(pago.credito.tasa_interes),
                    'cantidad_cuotas': pago.credito.cantidad_cuotas,
                    'tipo_plazo': pago.credito.get_tipo_plazo_display() if hasattr(pago.credito, 'tipo_plazo') else 'N/A',
                }
            })
        
        # Debug: agregar información de depuración
        print(f"Cobrador: {cobrador.nombre_completo}")
        print(f"Fechas: {fecha_desde} a {fecha_hasta}")
        print(f"Total pagos encontrados: {cantidad_pagos}")
        print(f"Total recaudado: {total_recaudado}")
        
        return JsonResponse({
            'success': True,
            'cobrador': {
                'id': cobrador.id,
                'nombre': cobrador.nombre_completo,
                'meta_diaria': float(cobrador.meta_diaria) if cobrador.meta_diaria else 0,
                'comision_porcentaje': float(cobrador.comision_porcentaje) if cobrador.comision_porcentaje else 0,
            },
            'estadisticas': {
                'total_recaudado': float(total_recaudado),
                'cantidad_pagos': cantidad_pagos,
                'promedio_pago': float(promedio_pago),
                'creditos_unicos': creditos_unicos,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
            },
            'pagos': pagos_data,
            'tiene_mas_pagos': pagos.count() > 50,
        })
        
    except Exception as e:
        print(f"Error en detalles_pagos_cobrador: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': f'Error al cargar los datos: {str(e)}'
        })
