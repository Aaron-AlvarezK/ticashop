from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # LISTAR PEDIDOS
    # =========================
    path('pedidos/', views.listar_pedidos, name='listar_pedidos'),

    # =========================
    # NUEVO FLUJO DE CREACIÓN
    # =========================
    # Paso 1: Crear pedido vacío (sin pedido_id aún)
    path('pedidos/nuevo/', views.crear_pedido_inicial, name='crear_pedido_inicial'),
    
    # Paso 2: Datos del documento (ya con pedido_id)
    path('pedidos/<int:pedido_id>/datos/', views.crear_pedido_datos, name='crear_pedido_datos'),

    # Paso 3: Agregar productos y confirmar
    path('pedidos/<int:pedido_id>/productos/', views.agregar_productos_pedido, name='agregar_productos_pedido'),

    # =========================
    # CARRITO POR PEDIDO
    # =========================
    path('pedidos/<int:pedido_id>/eliminar-producto/<int:producto_id>/', views.eliminar_producto_carrito, name='eliminar_producto_carrito'),

    # =========================
    # DETALLE DEL PEDIDO
    # =========================
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('pedidos/<int:pedido_id>/enviar/', views.marcar_pedido_enviado, name='marcar_pedido_enviado'),
    
    # =========================
    # ESTADÍSTICAS Y EXPORTAR
    # =========================
    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    path('exportar-excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
]