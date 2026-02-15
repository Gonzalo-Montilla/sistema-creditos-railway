# Pagaré electrónico - firma OTP por deudor y codeudor
# Genera PDF: Pagaré en blanco + Carta de instrucciones

import hashlib
import random
import string
from datetime import timedelta
from io import BytesIO
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings

from .models import Credito, PagareOTP


OTP_LENGTH = 6
OTP_VALID_MINUTES = 15


def _generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def _hash_otp(otp):
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def _verify_otp(plain_otp, otp_hash):
    return _hash_otp(plain_otp) == otp_hash


def _get_pending_otp(credito_id, tipo_firmante):
    now = timezone.now()
    return PagareOTP.objects.filter(
        credito_id=credito_id,
        tipo_firmante=tipo_firmante,
        expires_at__gt=now,
    ).order_by('-created_at').first()


def solicitar_otp_pagare(credito_id):
    """
    Genera OTP para cliente y codeudor (si existe), envía correos.
    Retorna: {
        'success': bool,
        'cliente': {'otp': str, 'celular': str, 'email_enviado': bool, 'message': str},
        'codeudor': {...} or None,
        'message': str
    }
    """
    credito = Credito.objects.filter(id=credito_id).first()
    if not credito or credito.estado != 'APROBADO':
        return {'success': False, 'message': 'Crédito no encontrado o no está aprobado.'}

    if credito.tiene_pagare_firmado():
        return {'success': False, 'message': 'El pagaré de este crédito ya está firmado.'}

    resultado = {'success': True, 'cliente': None, 'codeudor': None, 'message': ''}
    cliente = credito.cliente

    # Invalidar OTPs anteriores de este crédito
    PagareOTP.objects.filter(credito_id=credito_id).delete()

    # OTP Cliente
    otp_cli = _generate_otp()
    expires_at = timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)
    PagareOTP.objects.create(
        credito=credito,
        tipo_firmante='cliente',
        otp_hash=_hash_otp(otp_cli),
        expires_at=expires_at,
    )
    email_cli = (cliente.email or '').strip()
    cel_cli = (cliente.celular or '').strip()
    email_enviado_cli = False
    if email_cli:
        try:
            asunto = 'Código de verificación - Firma de pagaré'
            cuerpo = (
                f'Hola {cliente.nombre_completo},\n\n'
                f'Su código para firmar el pagaré del crédito #{credito.id} es:\n\n  {otp_cli}\n\n'
                f'Válido por {OTP_VALID_MINUTES} minutos.\n\nAtentamente,\nSistema de Créditos'
            )
            EmailMessage(
                asunto, cuerpo,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                [email_cli],
            ).send(fail_silently=False)
            email_enviado_cli = True
        except Exception:
            pass
    resultado['cliente'] = {
        'otp': otp_cli,
        'celular': cel_cli,
        'email_enviado': email_enviado_cli,
        'message': f'Código enviado a {email_cli}' if email_enviado_cli else 'Sin correo; use WhatsApp.',
    }

    # OTP Codeudor (si existe)
    try:
        codeudor = credito.cliente.codeudor
    except Exception:
        codeudor = None

    if codeudor:
        otp_cod = _generate_otp()
        PagareOTP.objects.create(
            credito=credito,
            tipo_firmante='codeudor',
            otp_hash=_hash_otp(otp_cod),
            expires_at=expires_at,
        )
        email_cod = (getattr(codeudor, 'email', None) or '').strip()
        cel_cod = (codeudor.celular or '').strip()
        email_enviado_cod = False
        if email_cod:
            try:
                asunto = 'Código de verificación - Firma de pagaré (codeudor)'
                cuerpo = (
                    f'Hola {codeudor.nombre_completo},\n\n'
                    f'Su código para firmar el pagaré del crédito #{credito.id} es:\n\n  {otp_cod}\n\n'
                    f'Válido por {OTP_VALID_MINUTES} minutos.\n\nAtentamente,\nSistema de Créditos'
                )
                EmailMessage(
                    asunto, cuerpo,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                    [email_cod],
                ).send(fail_silently=False)
                email_enviado_cod = True
            except Exception:
                pass
        resultado['codeudor'] = {
            'otp': otp_cod,
            'celular': cel_cod,
            'email_enviado': email_enviado_cod,
            'message': f'Código enviado a {email_cod}' if email_enviado_cod else 'Sin correo; use WhatsApp.',
        }
    else:
        resultado['codeudor'] = None

    resultado['message'] = 'Códigos generados. Indique a cada firmante que ingrese su código.'
    return resultado


def validar_otp_pagare(credito_id, tipo_firmante, otp_ingresado):
    """
    Valida el OTP del cliente o codeudor. Si con esta firma ya están todos, genera PDF y envía correo.
    Retorna (True, None) o (False, mensaje_error).
    """
    registro = _get_pending_otp(credito_id, tipo_firmante)
    if not registro:
        return False, 'El código ha expirado o no existe. Solicite uno nuevo.'

    if not _verify_otp((otp_ingresado or '').strip(), registro.otp_hash):
        return False, 'Código incorrecto. Verifique e intente de nuevo.'

    credito = Credito.objects.get(id=credito_id)
    now = timezone.now()

    if tipo_firmante == 'cliente':
        credito.pagare_firmado_cliente = now
        credito.save(update_fields=['pagare_firmado_cliente'])
    else:
        credito.pagare_firmado_codeudor = now
        credito.save(update_fields=['pagare_firmado_codeudor'])

    registro.delete()

    # ¿Falta que firme alguien?
    try:
        credito.cliente.codeudor
        tiene_codeudor = True
    except Exception:
        tiene_codeudor = False

    if tiene_codeudor and not credito.pagare_firmado_codeudor:
        return True, None  # Falta codeudor
    if not credito.pagare_firmado_cliente:
        return True, None  # No debería pasar

    # Todos firmaron: generar PDF, guardar, enviar correo
    codigo = f"PG-{timezone.now().year}-{credito.id:06d}"
    pdf_file = generar_pdf_pagare(credito, codigo=codigo)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    from django.core.files.base import ContentFile
    nombre_archivo = f'pagare_credito_{credito.id}_{now.strftime("%Y%m%d_%H%M")}.pdf'
    credito.documento_pagare.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    credito.fecha_firma_pagare = now
    credito.codigo_pagare = codigo
    credito.save(update_fields=['documento_pagare', 'fecha_firma_pagare', 'codigo_pagare'])

    # Enviar correo al cliente (y codeudor si tiene email) con PDF adjunto
    for person, email in [(credito.cliente, (credito.cliente.email or '').strip())]:
        if email:
            try:
                asunto = 'Pagaré firmado - Crédito #%s' % credito.id
                cuerpo = (
                    'Se informa que se firmó un pagaré en blanco con carta de instrucciones '
                    'correspondiente al crédito #%s. Adjunto encontrará el documento.\n\n'
                    'Atentamente,\nSistema de Créditos' % credito.id
                )
                em = EmailMessage(
                    asunto, cuerpo,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                    [email],
                )
                pdf_file.seek(0)
                em.attach(nombre_archivo, pdf_file.getvalue(), 'application/pdf')
                em.send(fail_silently=False)
            except Exception:
                pass
    if tiene_codeudor:
        codeudor = credito.cliente.codeudor
        email_cod = (getattr(codeudor, 'email', None) or '').strip()
        if email_cod:
            try:
                pdf_file.seek(0)
                asunto = 'Pagaré firmado - Crédito #%s (codeudor)' % credito.id
                cuerpo = (
                    'Se informa que se firmó un pagaré en blanco con carta de instrucciones '
                    'correspondiente al crédito #%s. Adjunto encontrará el documento.\n\n'
                    'Atentamente,\nSistema de Créditos' % credito.id
                )
                em_cod = EmailMessage(
                    asunto, cuerpo,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                    [email_cod],
                )
                em_cod.attach(nombre_archivo, pdf_file.getvalue(), 'application/pdf')
                em_cod.send(fail_silently=False)
            except Exception:
                pass

    return True, None


def regenerar_pdf_pagare(credito_id):
    """
    Regenera el PDF del pagaré con el formato actual (páginas independientes + anexo cédulas/datos).
    Mantiene codigo_pagare y fecha_firma_pagare. Retorna (True, None) o (False, mensaje_error).
    """
    credito = Credito.objects.filter(id=credito_id).first()
    if not credito or not credito.documento_pagare:
        return False, 'No hay documento de pagaré para regenerar.'

    codigo = getattr(credito, 'codigo_pagare', None) or f"PG-{timezone.now().year}-{credito.id:06d}"
    pdf_file = generar_pdf_pagare(credito, codigo=codigo)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    from django.core.files.base import ContentFile
    nombre_archivo = f'pagare_credito_{credito.id}_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
    credito.documento_pagare.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    credito.codigo_pagare = codigo
    credito.save(update_fields=['documento_pagare', 'codigo_pagare'])
    return True, None


def _numero_a_letras(num):
    """Convierte un número entero a letras (español, simplificado)."""
    unidades = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
    especiales = ['diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve']
    decenas = ['', '', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    if num == 0:
        return 'cero'
    if num < 0 or num > 999999999:
        return str(num)
    if num < 10:
        return unidades[num]
    if num < 20:
        return especiales[num - 10]
    if num < 100:
        d, u = divmod(num, 10)
        return (decenas[d] + (' y ' + unidades[u] if u else '')).strip()
    if num < 1000:
        c, r = divmod(num, 100)
        if c == 1:
            pre = 'ciento ' if r else 'cien'
        else:
            pre = (unidades[c] if c else '') + 'cientos '
        return (pre + _numero_a_letras(r)).strip() if r else pre.strip()
    if num < 1000000:
        m, r = divmod(num, 1000)
        pre = (_numero_a_letras(m) + ' mil ') if m != 1 else 'mil '
        return (pre + _numero_a_letras(r)).strip() if r else pre.strip()
    mill, r = divmod(num, 1000000)
    pre = (_numero_a_letras(mill) + ' millón ') if mill != 1 else 'un millón '
    return (pre + _numero_a_letras(r)).strip() if r else pre.strip()


def generar_pdf_pagare(credito, codigo=None):
    """
    Genera el PDF del pagaré en blanco + carta de instrucciones.
    Incluye tabla de firmantes (cliente + codeudor si hay) y fotos tipo documento.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

    if codigo is None:
        codigo = getattr(credito, 'codigo_pagare', None) or f"PG-{timezone.now().year}-{credito.id:06d}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    small = ParagraphStyle('Small', parent=normal, fontSize=8, spaceAfter=3)
    small_bold = ParagraphStyle('SmallBold', parent=small, fontName='Helvetica-Bold')
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=12, spaceAfter=6, alignment=1)

    # Datos comunes
    cliente = credito.cliente
    try:
        codeudor = credito.cliente.codeudor
    except Exception:
        codeudor = None
    ciudad = (cliente.barrio or cliente.direccion or 'Colombia')[:50]
    fecha_suscripcion = (credito.fecha_firma_pagare or timezone.now()).strftime('%Y/%m/%d')
    fecha_creacion = fecha_suscripcion
    valor_num = int(credito.monto)
    valor_letras = _numero_a_letras(valor_num).upper() + ' PESOS M/CTE'
    valor_str = f'${credito.monto:,.0f}'.replace(',', '.')
    acreedor_nombre = getattr(settings, 'NOMBRE_ENTIDAD_PAGARE', '_______________________________________')
    ref_entidad = getattr(settings, 'REFERENCIA_PAGARE_ENTIDAD', str(credito.id))

    firmantes = []
    firmantes.append((cliente.nombre_completo, 'CC', cliente.cedula, 'OTORGANTE'))
    if codeudor:
        firmantes.append((codeudor.nombre_completo, 'CC', codeudor.cedula, 'OTORGANTE'))

    def tabla_firmantes():
        data = [['Nombre', 'Tipo identificación', 'Número', 'Rol']]
        for nom, tipo, num, rol in firmantes:
            data.append([nom, tipo, num, rol])
        t = Table(data, colWidths=[2.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    def fila_firma_con_foto(nombre_completo, tipo_doc, numero_doc, ruta_foto=None):
        """Una fila: foto (1" x 1.2") a la izquierda, datos de firma a la derecha."""
        try:
            if ruta_foto and hasattr(ruta_foto, 'path'):
                img = Image(ruta_foto.path, width=1 * inch, height=1.2 * inch)
            else:
                img = Paragraph('<br/><br/>Sin foto', small)
        except Exception:
            img = Paragraph('<br/><br/>Sin foto', small)
        texto_datos = (
            f'Nombre del firmante: {nombre_completo}<br/>'
            'Calidad en que firma: OTORGANTE<br/>'
            f'Tipo de documento: {tipo_doc}<br/>'
            f'Identificación: {numero_doc}<br/>'
            'Nombre Persona Representada: N/A<br/>'
            'Num Documento Persona Representada: N/A<br/>'
            'Tipo Documento Persona Representada: N/A'
        )
        t = Table([[img, Paragraph(texto_datos, small)]], colWidths=[1.2 * inch, 3.5 * inch])
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOX', (0, 0), (-1, -1), 0.5, colors.grey)]))
        return t

    flow = []

    # ========== PARTE 1: PAGARÉ EN BLANCO ==========
    flow.append(Paragraph('PAGARÉ EN BLANCO', titulo))
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(Paragraph(f'PAGARÉ NÚMERO: {codigo}', small_bold))
    flow.append(Paragraph(f'REFERENCIA PAGARÉ: {ref_entidad}', small_bold))
    flow.append(Spacer(1, 0.08 * inch))
    flow.append(Paragraph(f'Ciudad {ciudad} y fecha {fecha_suscripcion}', small))
    flow.append(Paragraph('Señores', small))
    flow.append(Paragraph(acreedor_nombre, small))
    flow.append(Paragraph('E. S. M', small))
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(Paragraph(
        'Referencia: Autorización e instrucciones para llenar un Pagaré de contragarantía firmado con espacios en blanco.',
        small,
    ))
    flow.append(Paragraph('Yo, (Nosotros):', small_bold))
    flow.append(tabla_firmantes())
    flow.append(Spacer(1, 0.08 * inch))
    texto_autorizacion = (
        'Por medio de este documento y en los términos del artículo 622 de Código de Comercio autorizo a ustedes en forma permanente e irrevocable para llenar el documento (pagaré) que hemos otorgado a su favor. El documento (pagaré) tiene espacios en blanco que podrán ser llenados sin previo aviso. '
        'En el espacio reservado para nombre de las personas a quienes deba hacerse el pago se indicará el nombre de %s. '
        'En los espacios reservados para un valor en pesos se indicará el monto de cualquier suma insoluta, presente o futura, que para la fecha en que sea llenado el pagaré llegare a deber. '
        'La fecha del vencimiento y la fecha de emisión del pagaré serán las que los acreedores indiquen al llenarlo. '
        'Los acreedores quedan facultados para dar por vencidos los plazos y proceder al cobro por vía judicial o extrajudicial en los casos: (a) incumplimiento de obligaciones; (b) embargo o persecución de bienes; (c) concordato o liquidación; (d) muerte del firmante; (e) desaparición de garantías; (f) falta de información; (g) cesación de pagos. '
        '6. El lugar de cumplimiento será el de las oficinas de los acreedores. '
        '7. Autorizo a %s o a quien represente sus derechos a reportar a CIFIN u otras centrales de información comercial mi endeudamiento. '
        'Acompaño el documento (pagaré) en referencia debidamente firmado y declaro haber recibido copia de la presente carta de instrucciones.'
    ) % (acreedor_nombre, acreedor_nombre)
    flow.append(Paragraph(texto_autorizacion.replace('. ', '.<br/>'), small))
    flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph('Atentamente,', small_bold))
    flow.append(Spacer(1, 0.08 * inch))
    flow.append(fila_firma_con_foto(cliente.nombre_completo, 'CC', cliente.cedula, getattr(cliente, 'foto_rostro', None)))
    if codeudor:
        flow.append(Spacer(1, 0.15 * inch))
        flow.append(fila_firma_con_foto(codeudor.nombre_completo, 'CC', codeudor.cedula, getattr(codeudor, 'foto_rostro', None)))

    # Página independiente para la Carta de instrucciones
    flow.append(PageBreak())

    # ========== PARTE 2: CARTA DE INSTRUCCIONES (Pagaré) ==========
    flow.append(Paragraph('CARTA DE INSTRUCCIONES', titulo))
    flow.append(Paragraph('PAGARÉ NÚMERO: %s' % codigo, small_bold))
    flow.append(Paragraph('REFERENCIA PAGARÉ: %s' % ref_entidad, small_bold))
    flow.append(Spacer(1, 0.08 * inch))
    flow.append(Paragraph(f'VALOR {valor_str}', small_bold))
    flow.append(Paragraph('Yo (nosotros),', small_bold))
    flow.append(tabla_firmantes())
    flow.append(Spacer(1, 0.08 * inch))
    texto_pagare = (
        f'Me (nos) obligo (obligamos) incondicionalmente (y de manera solidaria) a pagar en dinero efectivo a {acreedor_nombre} (en adelante el (los) "Acreedor (es)") o a su orden, a quien represente sus derechos, en la ciudad de {ciudad}, {fecha_creacion} la suma de ({valor_str}) {valor_letras}. '
        'A partir de la fecha de este título y sin perjuicio de las acciones legales del tenedor encaminadas a su cobro, sobre el saldo de capital pendiente de pago se causarán intereses de mora a la tasa de interés de mora más alta permitida por la Ley. Todos los gastos e impuestos que cause este título-valor, así como los honorarios de abogado y las costas del cobro, son de mi (nuestro) cargo. '
        'Los Acreedores están autorizados para debitar de cualquier suma a mi (nuestro) favor el importe total o parcial de este título-valor, por vía de compensación. Renuncio (renunciamos) en forma expresa, a favor de(l) (los) Acreedores, a los derechos de nombrar secuestre de bienes en caso de cobro judicial y de solicitar que los bienes embargados se dividan en lotes para la subasta pública. Para todos los efectos legales, reconozco (reconocemos) que la obligación contraída tiene carácter de indivisible. Hago (hacemos) constar que la solidaridad y la indivisibilidad subsisten en caso de prórroga o de cualquier modificación de lo estipulado, aunque se pacta con uno solo de los deudores. Queda excusado el protesto de este pagaré. '
        'Se emite este pagaré el día %s y se entrega con la intención de hacerlo negociable.' % fecha_suscripcion
    )
    flow.append(Paragraph(texto_pagare, small))
    flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph('Atentamente,', small_bold))
    flow.append(Spacer(1, 0.08 * inch))
    flow.append(fila_firma_con_foto(cliente.nombre_completo, 'CC', cliente.cedula, getattr(cliente, 'foto_rostro', None)))
    if codeudor:
        flow.append(Spacer(1, 0.15 * inch))
        flow.append(fila_firma_con_foto(codeudor.nombre_completo, 'CC', codeudor.cedula, getattr(codeudor, 'foto_rostro', None)))

    flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph('&bull; Firmado digitalmente mediante verificación OTP. Documento generado por el sistema.', ParagraphStyle('Disclaimer', parent=small, fontSize=7, alignment=1, textColor=colors.grey)))

    # Página independiente: Anexo documental (cédulas + datos básicos)
    flow.append(PageBreak())

    # ========== PARTE 3: ANEXO - DOCUMENTOS DE IDENTIDAD ==========
    flow.append(Paragraph('ANEXO - DOCUMENTOS DE IDENTIDAD', titulo))
    flow.append(Paragraph('Pagaré Nº %s — Crédito #%s' % (codigo, credito.id), small))
    flow.append(Spacer(1, 0.2 * inch))

    def _imagen_o_placeholder(field, ancho=2 * inch, alto=1.25 * inch):
        try:
            if field and hasattr(field, 'path'):
                return Image(field.path, width=ancho, height=alto)
            return Paragraph('<br/><br/>Sin imagen', small)
        except Exception:
            return Paragraph('<br/><br/>Sin imagen', small)

    def _bloque_anexo_firmante(nombre_rol, persona):
        """Una sección: título, cédula frontal/trasera, resumen de datos."""
        flow.append(Paragraph(nombre_rol, ParagraphStyle('AnexoSub', parent=small_bold, fontSize=10, spaceAfter=8)))
        # Fotos cédula (lado a lado) con leyenda bajo cada una
        img_frente = _imagen_o_placeholder(getattr(persona, 'foto_cedula_frontal', None))
        img_trasera = _imagen_o_placeholder(getattr(persona, 'foto_cedula_trasera', None))
        cap_frente = Paragraph('Cédula frente', ParagraphStyle('Cap', parent=small, fontSize=7, alignment=1))
        cap_trasera = Paragraph('Cédula reverso', ParagraphStyle('Cap', parent=small, fontSize=7, alignment=1))
        tbl_fotos = Table(
            [[img_frente, img_trasera], [cap_frente, cap_trasera]],
            colWidths=[2 * inch, 2 * inch],
        )
        tbl_fotos.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (1, 1), 'CENTER'),
        ]))
        flow.append(tbl_fotos)
        flow.append(Spacer(1, 0.08 * inch))
        # Resumen datos básicos
        datos = [
            ['Nombre', persona.nombre_completo],
            ['Documento (CC)', getattr(persona, 'cedula', '—')],
            ['Dirección', (getattr(persona, 'direccion', None) or '—')[:60]],
            ['Celular', (getattr(persona, 'celular', None) or '—')],
        ]
        if getattr(persona, 'email', None):
            datos.append(['Correo', persona.email])
        if getattr(persona, 'barrio', None):
            datos.append(['Barrio', persona.barrio])
        t_datos = Table(datos, colWidths=[1.5 * inch, 4 * inch])
        t_datos.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        flow.append(t_datos)
        flow.append(Spacer(1, 0.25 * inch))

    _bloque_anexo_firmante('Cliente (deudor)', cliente)
    if codeudor:
        _bloque_anexo_firmante('Codeudor', codeudor)

    try:
        doc.build(flow)
        buffer.seek(0)
        return buffer
    except Exception:
        return None
