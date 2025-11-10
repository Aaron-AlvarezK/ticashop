from django.db import models
from django.utils import timezone

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
    )
    
    MEDIOS_PAGO = (
        ('Efectivo', 'Efectivo'),
        ('Tarjeta de Débito', 'Tarjeta de Débito'),
        ('Tarjeta de Crédito', 'Tarjeta de Crédito'),
        ('Transferencia', 'Transferencia'),
    )
    
    # Información del documento
    tipo_documento = models.CharField(max_length=7, choices=TIPOS_DOCUMENTO)
    folio = models.IntegerField(verbose_name='Folio')
    
    # Relaciones
    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.CASCADE,
        verbose_name='Cliente'
    )
    vendedor = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Vendedor'
    )
    pedido = models.OneToOneField(
        'ventas.Pedido', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        unique=True,
        verbose_name='Pedido asociado'
    )
    
    # Montos
    neto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Neto', default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='IVA', default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total', default=0)
    
    # Estado y fechas
    estado = models.CharField(
        max_length=12, 
        choices=ESTADOS_DOCUMENTO, 
        default='Emitida'
    )
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name='Fecha emisión')
    fecha_vencimiento = models.DateField(
        blank=True, 
        null=True,
        verbose_name='Fecha vencimiento'
    )
    
    # Información específica
    medio_de_pago = models.CharField(
        max_length=20, 
        choices=MEDIOS_PAGO, 
        blank=True, 
        null=True,
        verbose_name='Medio de pago'
    )
    
    def __str__(self):
        return f"{self.tipo_documento} #{self.folio} - {self.cliente.razon_social}"
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de pago"""
        try:
            total_pagado = sum(pago.monto_pagado for pago in self.pagos.all())
            return max(self.total - total_pagado, 0)  # No negativo
        except:
            return self.total
    
    @property
    def porcentaje_pagado(self):
        """Calcula el porcentaje pagado del documento"""
        try:
            if self.total and self.total > 0:
                total_pagado = sum(pago.monto_pagado for pago in self.pagos.all())
                return (total_pagado / self.total) * 100
            return 0
        except:
            return 0
    
    def esta_vencida(self):
        """Verifica si la factura está vencida"""
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
    documento = models.ForeignKey(
        DocumentoVenta, 
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        'productos.Producto', 
        on_delete=models.CASCADE,
        verbose_name='Producto'
    )
    cantidad = models.IntegerField(default=1)
    precio_unitario_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Precio unitario'
    )
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name='Subtotal'
    )
    costo_unitario_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True, 
        null=True,
        verbose_name='Costo unitario al momento de la venta'
    )
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal al guardar"""
        self.subtotal = self.cantidad * self.precio_unitario_venta
        
        # Guardar el costo del producto al momento de la venta
        if not self.costo_unitario_venta and self.producto:
            self.costo_unitario_venta = self.producto.costo_unitario
            
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'detalle_documento'
        verbose_name = 'Detalle de Documento'
        verbose_name_plural = 'Detalles de Documento'

class Pago(models.Model):
    documento = models.ForeignKey(
        DocumentoVenta, 
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    fecha_pago = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de pago')
    monto_pagado = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name='Monto pagado'
    )
    metodo_pago = models.CharField(
        max_length=50, 
        verbose_name='Método de pago'
    )
    referencia = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Referencia/Número de operación'
    )
    observaciones = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Observaciones'
    )
    
    def __str__(self):
        return f"Pago #{self.id} - {self.monto_pagado}"
    
    def save(self, *args, **kwargs):
        """Actualiza el estado del documento después de guardar el pago"""
        super().save(*args, **kwargs)
        self.actualizar_estado_documento()
    
    def actualizar_estado_documento(self):
        """Actualiza el estado del documento basado en los pagos"""
        try:
            documento = self.documento
            total_pagado = sum(pago.monto_pagado for pago in documento.pagos.all())
            
            if total_pagado >= documento.total:
                documento.estado = 'Pagada'
            elif total_pagado > 0:
                documento.estado = 'Pago Parcial'
            elif documento.esta_vencida():
                documento.estado = 'Vencida'
            else:
                documento.estado = 'Emitida'
                
            documento.save()
        except:
            pass  # Evitar errores en caso de problemas
    
    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']