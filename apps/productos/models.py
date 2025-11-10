from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'


class Producto(models.Model):
    # Información básica
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    
    # Categorización
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Categoría'
    )
    
    # Precios y costos
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Precio de venta'
    )
    costo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Costo unitario'
    )
    
    # Inventario
    stock = models.IntegerField(default=0, verbose_name='Stock disponible')
    stock_minimo = models.IntegerField(default=0, verbose_name='Stock mínimo')
    
    # Proveedor
    proveedor = models.ForeignKey(
        'clientes.Proveedor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Proveedor'
    )
    
    # Impuestos y estado
    afecto_iva = models.BooleanField(default=True, verbose_name='Afecto a IVA')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def tiene_stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo and self.stock_minimo > 0
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        if self.costo_unitario > 0:
            return ((self.precio_unitario - self.costo_unitario) / self.costo_unitario) * 100
        return 0
    
    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['codigo']