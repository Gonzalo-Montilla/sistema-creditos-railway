# Habeas Data - Ley 1581 de 2012 / Decreto 1377 de 2013
# Autorización de tratamiento de datos personales (firma digital por OTP)

import hashlib
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from io import BytesIO

from .models import Cliente, Codeudor, HabeasDataOTP


OTP_LENGTH = 6
OTP_VALID_MINUTES = 15


def _generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def _hash_otp(otp):
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def _verify_otp(plain_otp, otp_hash):
    return _hash_otp(plain_otp) == otp_hash


def _get_pending_otp(tipo, objeto_id):
    now = timezone.now()
    qs = HabeasDataOTP.objects.filter(tipo=tipo, objeto_id=objeto_id, expires_at__gt=now)
    return qs.order_by('-created_at').first()


def solicitar_otp_habeas_data(tipo, objeto_id):
    """
    Genera OTP, lo guarda (hash + expiración), envía correo si hay email.
    Retorna: (otp_plain, email_enviado, celular, email_destino).
    Invalida cualquier OTP anterior para el mismo tipo+objeto_id.
    """
    if tipo == 'cliente':
        obj = Cliente.objects.filter(id=objeto_id).first()
        if not obj:
            return None, False, '', ''
        email_destino = (obj.email or '').strip()
        celular = (obj.celular or '').strip()
        nombre = obj.nombre_completo
    else:
        obj = Codeudor.objects.filter(id=objeto_id).first()
        if not obj:
            return None, False, '', ''
        email_destino = (obj.email or '').strip() if hasattr(obj, 'email') else ''
        celular = (obj.celular or '').strip()
        nombre = obj.nombre_completo

    # Invalidar OTPs anteriores
    HabeasDataOTP.objects.filter(tipo=tipo, objeto_id=objeto_id).delete()

    otp_plain = _generate_otp()
    expires_at = timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)
    HabeasDataOTP.objects.create(
        tipo=tipo,
        objeto_id=objeto_id,
        otp_hash=_hash_otp(otp_plain),
        expires_at=expires_at,
    )

    email_enviado = False
    if email_destino:
        try:
            asunto = 'Código de verificación - Autorización tratamiento de datos (Habeas Data)'
            cuerpo = (
                f'Hola {nombre},\n\n'
                f'Su código de verificación para la autorización de tratamiento de datos personales '
                f'(Ley 1581 de 2012 - Habeas Data) es:\n\n'
                f'  {otp_plain}\n\n'
                f'Este código es válido por {OTP_VALID_MINUTES} minutos.\n\n'
                f'Si no solicitó este código, puede ignorar este mensaje.\n\n'
                f'Atentamente,\nSistema de Créditos'
            )
            email = EmailMessage(
                asunto,
                cuerpo,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                [email_destino],
                reply_to=[getattr(settings, 'DEFAULT_FROM_EMAIL', None)] or [],
            )
            email.send(fail_silently=False)
            email_enviado = True
        except Exception:
            email_enviado = False

    return otp_plain, email_enviado, celular, email_destino


def validar_otp_y_firmar(tipo, objeto_id, otp_ingresado):
    """
    Valida el OTP; si es correcto genera el PDF, lo guarda en el modelo,
    envía correo con PDF adjunto y elimina el OTP. Retorna (True, None) o (False, mensaje_error).
    """
    registro = _get_pending_otp(tipo, objeto_id)
    if not registro:
        return False, 'El código ha expirado o no existe. Solicite uno nuevo.'

    if not _verify_otp(otp_ingresado.strip(), registro.otp_hash):
        return False, 'Código incorrecto. Verifique e intente de nuevo.'

    if tipo == 'cliente':
        obj = Cliente.objects.filter(id=objeto_id).first()
    else:
        obj = Codeudor.objects.filter(id=objeto_id).first()

    if not obj:
        return False, 'Registro no encontrado.'

    # Código único del documento (HD-YYYY-C000001 o HD-YYYY-D000001)
    now = timezone.now()
    prefijo = 'C' if tipo == 'cliente' else 'D'
    codigo = f"HD-{now.year}-{prefijo}{obj.id:06d}"

    # Generar PDF (incluye código, disclaimer y sección de firma organizada)
    pdf_file = generar_pdf_habeas_data(tipo, obj, codigo=codigo)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    # Guardar en el modelo
    from django.core.files.base import ContentFile
    nombre_archivo = f'habeas_data_{tipo}_{objeto_id}_{now.strftime("%Y%m%d_%H%M")}.pdf'
    obj.documento_habeas_data.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    obj.fecha_autorizacion_habeas_data = now
    obj.codigo_habeas_data = codigo
    obj.save(update_fields=['documento_habeas_data', 'fecha_autorizacion_habeas_data', 'codigo_habeas_data'])

    # Enviar correo con PDF adjunto
    email_destino = ''
    if tipo == 'cliente':
        email_destino = (obj.email or '').strip()
    else:
        email_destino = (getattr(obj, 'email', None) or '').strip()
    if email_destino:
        try:
            asunto = 'Su autorización de tratamiento de datos (Habeas Data)'
            cuerpo = (
                f'Adjunto encontrará el documento que acredita su autorización de tratamiento de datos personales '
                f'(Ley 1581 de 2012 - Habeas Data), firmada digitalmente el día de hoy.\n\n'
                f'Conserve este documento para sus registros.\n\n'
                f'Atentamente,\nSistema de Créditos'
            )
            email = EmailMessage(
                asunto,
                cuerpo,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                [email_destino],
            )
            pdf_file.seek(0)
            email.attach(nombre_archivo, pdf_file.getvalue(), 'application/pdf')
            email.send(fail_silently=False)
        except Exception:
            pass  # No fallar si el correo no se envía; el PDF ya está guardado

    registro.delete()
    return True, None


def generar_pdf_habeas_data(tipo, obj, codigo=None, fecha_firma=None):
    """
    Genera el PDF de la autorización Habeas Data.
    obj: instancia de Cliente o Codeudor.
    codigo: código único del documento (ej. HD-2025-C000123). Si no se pasa, se usa obj.codigo_habeas_data o se genera uno.
    fecha_firma: datetime a mostrar como fecha/hora de aceptación. Si no se pasa, se usa timezone.now().
    Retorna BytesIO con el PDF o None.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

    if codigo is None:
        codigo = getattr(obj, 'codigo_habeas_data', None) or (
            f"HD-{timezone.now().year}-{'C' if tipo == 'cliente' else 'D'}{obj.id:06d}"
        )
    if fecha_firma is None:
        fecha_firma = timezone.now()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=6,
        alignment=1,
    )
    normal = styles['Normal']
    normal_justified = ParagraphStyle('NormalJustified', parent=normal, alignment=TA_JUSTIFY)
    normal_small = ParagraphStyle('Small', parent=normal, fontSize=9, spaceAfter=4)
    normal_small_center = ParagraphStyle('SmallCenter', parent=normal_small, alignment=1)
    code_style = ParagraphStyle(
        'Code',
        parent=normal,
        fontSize=11,
        fontName='Helvetica-Bold',
        borderPadding=8,
        spaceAfter=4,
        alignment=1,
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=normal,
        fontSize=10,
        alignment=1,
        spaceAfter=4,
        spaceBefore=4,
    )

    flow = []

    # Título y referencia legal
    flow.append(Paragraph('AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES', title_style))
    flow.append(Paragraph('Ley 1581 de 2012 - Decreto 1377 de 2013 (Colombia)', normal_small))
    flow.append(Spacer(1, 0.15 * inch))

    # Código único de verificación (destacado)
    flow.append(Paragraph(f'Código de verificación del documento: <b>{codigo}</b>', normal_small))
    flow.append(Spacer(1, 0.25 * inch))

    # Texto de la ley
    texto_ley = (
        'En cumplimiento de la Ley 1581 de 2012 y el Decreto 1377 de 2013, el titular de los datos personales '
        'autoriza de manera previa, expresa e informada el tratamiento de sus datos personales por parte del responsable del tratamiento, '
        'para las finalidades propias de la relación crediticia y comercial (evaluación, aprobación, desembolso, cobro, reportes a centrales de riesgo cuando aplique, '
        'y gestión de cobranza). El titular ha sido informado sobre sus derechos a conocer, actualizar, rectificar y suprimir sus datos, '
        'revocar la autorización y presentar quejas ante la Superintendencia de Industria y Comercio.'
    )
    flow.append(Paragraph(texto_ley, normal_justified))
    flow.append(Spacer(1, 0.3 * inch))

    # Datos del titular + foto al lado (bien alineados)
    foto_rostro = getattr(obj, 'foto_rostro', None)
    img_celda = Paragraph('<br/><br/><i>Sin foto</i>', ParagraphStyle('Placeholder', parent=normal_small, alignment=1))
    if foto_rostro and hasattr(foto_rostro, 'path'):
        try:
            img_celda = Image(foto_rostro.path, width=1.1 * inch, height=1.35 * inch)
        except Exception:
            pass
    titulo_titular = '<b>Datos del titular (Cliente)</b>' if tipo == 'cliente' else '<b>Datos del titular (Codeudor)</b>'
    datos_titular = [
        [Paragraph(titulo_titular, normal), img_celda],
        [Paragraph(f'Nombre: {obj.nombre_completo}', normal_small), ''],
        [Paragraph(f'Documento de identidad: {obj.cedula}', normal_small), ''],
    ]
    tbl_titular = Table(datos_titular, colWidths=[4.2 * inch, 1.35 * inch], rowHeights=[None, None, None])
    tbl_titular.setStyle(TableStyle([
        ('SPAN', (1, 0), (1, 2)),  # foto ocupa las 3 filas a la derecha
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 6),
    ]))
    flow.append(tbl_titular)
    flow.append(Spacer(1, 0.35 * inch))

    # Línea separadora
    tbl_line = Table([['']], colWidths=[6.5 * inch], rowHeights=[4])
    tbl_line.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#cccccc'))]))
    flow.append(tbl_line)
    flow.append(Spacer(1, 0.2 * inch))

    # Sección FIRMA DIGITAL: disclaimer con icono y datos organizados
    fecha_hora = fecha_firma.strftime('%d/%m/%Y %H:%M') if hasattr(fecha_firma, 'strftime') else str(fecha_firma)
    flow.append(Paragraph(
        '<b>Firma digital</b>',
        ParagraphStyle('FirmaTitle', parent=normal, fontSize=10, alignment=1, spaceAfter=8),
    ))
    flow.append(Paragraph(
        '&bull; Firmado digitalmente mediante verificación OTP',
        disclaimer_style,
    ))
    flow.append(Paragraph(
        'Este documento fue firmado de forma electrónica mediante código de un solo uso (OTP) enviado al titular.',
        ParagraphStyle('Disclaimer2', parent=normal_small, fontSize=8, alignment=1, spaceAfter=6),
    ))
    flow.append(Paragraph(f'Fecha y hora de aceptación: {fecha_hora}', normal_small_center))
    flow.append(Spacer(1, 0.1 * inch))
    tbl_code = Table(
        [[Paragraph(f'<b>Código único</b><br/>{codigo}', code_style)]],
        colWidths=[2.5 * inch],
        rowHeights=[None],
    )
    tbl_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    flow.append(tbl_code)
    flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph(
        'Este documento puede verificarse con el responsable del tratamiento mediante el código indicado.',
        ParagraphStyle('VerifyNote', parent=normal_small, fontSize=8, alignment=1, textColor=colors.grey),
    ))
    flow.append(Spacer(1, 0.25 * inch))
    flow.append(Paragraph(
        'Este documento queda en custodia del responsable del tratamiento como constancia de la autorización otorgada.',
        ParagraphStyle('CustodiaJustificada', parent=normal_small, alignment=TA_JUSTIFY),
    ))

    try:
        doc.build(flow)
        buffer.seek(0)
        return buffer
    except Exception:
        return None


def regenerar_pdf_habeas_data(tipo, objeto_id):
    """
    Regenera el PDF de Habeas Data con el formato actual (código único, disclaimer, firma organizada).
    Usa la fecha de autorización ya guardada; asigna código si no existía.
    Retorna (True, None) o (False, mensaje_error).
    """
    if tipo == 'cliente':
        obj = Cliente.objects.filter(id=objeto_id).first()
    else:
        obj = Codeudor.objects.filter(id=objeto_id).first()

    if not obj or not obj.documento_habeas_data:
        return False, 'No hay documento de autorización Habeas Data para regenerar.'

    codigo = getattr(obj, 'codigo_habeas_data', None) or (
        f"HD-{obj.fecha_autorizacion_habeas_data.year}-{'C' if tipo == 'cliente' else 'D'}{obj.id:06d}"
        if obj.fecha_autorizacion_habeas_data else
        f"HD-{timezone.now().year}-{'C' if tipo == 'cliente' else 'D'}{obj.id:06d}"
    )

    pdf_file = generar_pdf_habeas_data(tipo, obj, codigo=codigo, fecha_firma=obj.fecha_autorizacion_habeas_data)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    from django.core.files.base import ContentFile
    nombre_archivo = f'habeas_data_{tipo}_{objeto_id}_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
    obj.documento_habeas_data.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    obj.codigo_habeas_data = codigo
    obj.save(update_fields=['documento_habeas_data', 'codigo_habeas_data'])
    return True, None
