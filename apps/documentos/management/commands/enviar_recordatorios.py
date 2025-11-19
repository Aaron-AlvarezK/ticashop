import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from apps.documentos.models import DocumentoVenta

# Configurar un logger para ver qué pasa
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Busca facturas por vencer y vencidas, y envía recordatorios por correo.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando tarea de recordatorios de pago...'))
        
        hoy = timezone.localdate()
        
        # --- 1. Buscar facturas POR VENCER (Ej: vencen en 3 días) ---
        fecha_limite_pronto = hoy + timedelta(days=3)
        facturas_por_vencer = DocumentoVenta.objects.filter(
            tipo_documento='Factura',
            estado__in=['Emitida', 'Pago Parcial'], # Solo las pendientes
            fecha_vencimiento=fecha_limite_pronto
        )

        for doc in facturas_por_vencer:
            self.enviar_correo_recordatorio(doc, 'por_vencer')

        # --- 2. Buscar facturas VENCIDAS ---
        facturas_vencidas = DocumentoVenta.objects.filter(
            tipo_documento='Factura',
            estado__in=['Emitida', 'Pago Parcial'], # Solo las pendientes
            fecha_vencimiento__lt=hoy  # Fecha de vencimiento es anterior a hoy
        )
        
        for doc in facturas_vencidas:
            self.enviar_correo_recordatorio(doc, 'vencida')

        # --- 3. (Opcional) Enviar resumen al administrador ---
        if facturas_por_vencer.count() > 0 or facturas_vencidas.count() > 0:
            self.enviar_resumen_admin(facturas_por_vencer, facturas_vencidas)

        self.stdout.write(self.style.SUCCESS('Tarea de recordatorios finalizada.'))

    def enviar_correo_recordatorio(self, documento, tipo_plantilla):
        """
        Prepara y envía un correo al cliente.
        """
        cliente = documento.cliente
        # Intentamos obtener el email de facturación, si no, el del perfil de usuario
        email_cliente = documento.cliente.email_facturacion or documento.cliente.user.email

        if not email_cliente:
            logger.warning(f"Factura #{documento.folio} no tiene email de cliente.")
            return

        if tipo_plantilla == 'por_vencer':
            asunto = f"Recordatorio: Tu Factura #{documento.folio} está por vencer"
            template_txt = 'documentos/email/recordatorio_por_vencer.txt'
        else: # 'vencida'
            asunto = f"Aviso de Vencimiento: Tu Factura #{documento.folio} está vencida"
            template_txt = 'documentos/email/recordatorio_vencida.txt'

        context = {
            'cliente_nombre': cliente.razon_social,
            'folio': documento.folio,
            'total': documento.total,
            'fecha_vencimiento': documento.fecha_vencimiento,
        }
        
        cuerpo_mensaje = render_to_string(template_txt, context)

        try:
            send_mail(
                asunto,
                cuerpo_mensaje,
                settings.DEFAULT_FROM_EMAIL, # Tu email (ej: "ventas@ticashop.cl")
                [email_cliente],             # Email del destinatario
                fail_silently=False,
            )
            logger.info(f"Correo enviado para Factura #{documento.folio} a {email_cliente}")
        except Exception as e:
            logger.error(f"Error al enviar correo para Factura #{documento.folio}: {e}")

    def enviar_resumen_admin(self, por_vencer, vencidas):
        """
        Envía un resumen de la cobranza a un correo de la empresa.
        """
        asunto = f"Resumen de Cobranza TicaShop - {timezone.localdate()}"
        context = {
            'facturas_por_vencer': por_vencer,
            'facturas_vencidas': vencidas,
            'total_por_vencer': por_vencer.count(),
            'total_vencidas': vencidas.count(),
        }
        cuerpo_mensaje = render_to_string('documentos/email/resumen_admin.txt', context)
        
        send_mail(
            asunto,
            cuerpo_mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER] # Se auto-envía al email de la empresa
        )