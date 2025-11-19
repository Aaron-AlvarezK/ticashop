# apps/documentos/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class DocumentoVenta(models.Model):
    TIPOS_DOCUMENTO = (
        ('Factura', 'Factura'),
        ('Boleta', 'Boleta'),
    )

    ESTADOS_DOCUMENTO = (
        ('Emitida', 'Emitida'),
        ('Pagada', 'Pagada'),
        ('Vencida', 'Vencida'),
        ('Anulada', 'Anulada'),
        ('Pago Parcial', 'Pago Parcial'),
        ('Devuelta', 'Devuelta'),
        ('Devuelta Parcial', 'Devuelta Parcial'),
    )

    MEDIOS_PAGO = (
        ('Efectivo', 'Efectivo'),
        ('Tarjeta de Débito', 'Tarjeta de Débito'),
        ('Tarjeta de Crédito', 'Tarjeta de Crédito'),
        ('Transferencia', 'Transferencia'),
    )

    tipo_documento = models.CharField(max_length=7, choices=TIPOS_DOCUMENTO)
    folio = models.IntegerField(verbose_name='Folio', null=True, blank=True)

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, verbose_name='Cliente')
    vendedor = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, verbose_name='Vendedor')
    pedido = models.OneToOneField('ventas.Pedido', on_delete=models.SET_NULL, null=True, blank=True, unique=True, verbose_name='Pedido asociado')

    neto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Neto', default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='IVA', default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total', default=0)

    estado = models.CharField(max_length=20, choices=ESTADOS_DOCUMENTO, default='Emitida')
    fecha_emision = models.DateTimeField(verbose_name='Fecha emisión', null=True, blank=True)
    fecha_vencimiento = models.DateField(blank=True, null=True, verbose_name='Fecha vencimiento')

    medio_de_pago = models.CharField(max_length=20, choices=MEDIOS_PAGO, blank=True, null=True, verbose_name='Medio de pago')

    razon_social = models.CharField(max_length=255, blank=True, null=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    giro = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.folio:
            ultimo = DocumentoVenta.objects.filter(tipo_documento=self.tipo_documento).order_by('-folio').first()
            if ultimo and ultimo.folio:
                self.folio = ultimo.folio + 1
            else:
                self.folio = 1000
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_documento} #{self.folio}"

    @property
    def saldo_pendiente(self):
        try:
            total_pagado = sum(pago.monto_pagado for pago in self.pagos.all())
            return max(self.total - total_pagado, 0)
        except:
            return self.total

    def esta_vencida(self):
        try:
            if self.fecha_vencimiento and self.estado in ['Emitida', 'Pago Parcial']:
                return timezone.now().date() > self.fecha_vencimiento
            return False
        except:
            return False

    class Meta:
        db_table = 'documentos_venta'
        verbose_name = 'Documento de Venta'
        verbose_name_plural = 'Documentos de Venta'
        unique_together = ['tipo_documento', 'folio']
        ordering = ['-fecha_emision']


class DetalleDocumento(models.Model):
    documento = models.ForeignKey(DocumentoVenta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, verbose_name='Producto')
    cantidad = models.IntegerField(default=1)
    precio_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Subtotal')
    costo_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Costo unitario al momento de la venta')

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad or 0) * (self.precio_unitario_venta or 0)
        if not self.costo_unitario_venta and self.producto:
            self.costo_unitario_venta = getattr(self.producto, 'costo_unitario', None)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'detalle_documento'
        verbose_name = 'Detalle de Documento'
        verbose_name_plural = 'Detalles de Documento'


class Pago(models.Model):
    documento = models.ForeignKey(DocumentoVenta, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de pago')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto pagado')
    metodo_pago = models.CharField(max_length=50, verbose_name='Método de pago')
    referencia = models.CharField(max_length=255, blank=True, null=True, verbose_name='Referencia/Número de operación')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    def __str__(self):
        return f"Pago #{self.id} - {self.monto_pagado}"

    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']


class NotaCredito(models.Model):
    ESTADOS = [
        ('Emitida', 'Emitida'),
        ('Aplicada', 'Aplicada'),
    ]

    factura = models.ForeignKey(DocumentoVenta, related_name='notas_credito', on_delete=models.CASCADE)
    folio = models.CharField(max_length=50, blank=True, null=True)
    fecha_emision = models.DateField(default=timezone.localdate)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    motivo = models.TextField()
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Emitida')
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'NC {self.id} - Fact: {self.factura_id} - ${self.monto}'


class DetalleNotaCredito(models.Model):
    nota = models.ForeignKey(NotaCredito, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('productos.Producto', on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    cantidad = models.IntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    def save(self, *args, **kwargs):
        self.subtotal = (self.precio_unitario or Decimal(0)) * (self.cantidad or 0)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'detalle_nota_credito'
        verbose_name = 'Detalle Nota de Crédito'
        verbose_name_plural = 'Detalles Nota de Crédito'