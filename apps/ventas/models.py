from django.db import models

class Pedido(models.Model):
    ESTADOS_PEDIDO = (
        ('Borrador', 'Borrador'),
        ('Pendiente', 'Pendiente'),
        ('Procesando', 'Procesando'), 
        ('Enviado', 'Enviado'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    )
    
    # Relaciones
    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.CASCADE,
        verbose_name='Cliente'
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Vendedor'
    )
    
    # Información del pedido
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_PEDIDO, 
        default='Pendiente'
    )
    
    # Información de envío/facturación
    direccion_despacho = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Dirección de despacho'
    )
    observaciones = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Observaciones'
    )
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.razon_social}"
    
    def calcular_total(self):
        """Calcula el total sumando los subtotales de los detalles"""
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save()
        return total
    
    @property
    def cantidad_items(self):
        """Retorna la cantidad total de items en el pedido"""
        return sum(detalle.cantidad for detalle in self.detalles.all())
    
    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_creacion']

class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
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
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal al guardar"""
        self.subtotal = self.cantidad * self.precio_unitario_venta
        super().save(*args, **kwargs)
        # Actualizar el total del pedido
        self.pedido.calcular_total()
    
    def delete(self, *args, **kwargs):
        """Actualiza el total del pedido al eliminar un detalle"""
        pedido = self.pedido
        super().delete(*args, **kwargs)
        pedido.calcular_total()
    
    class Meta:
        db_table = 'detalle_pedido'
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'