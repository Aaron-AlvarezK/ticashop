from django.urls import path
from . import views

app_name = 'ventas'
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
    path('pedidos/<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    
    # =========================
    # ESTADÍSTICAS Y EXPORTAR
    # =========================
    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    path('exportar-excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),

    path('cliente/cart/', views.cliente_view_cart, name='cliente_view_cart'),
    path('cliente/cart/add/<int:producto_id>/', views.cliente_add_to_cart, name='cliente_add_to_cart'),
    path('cliente/cart/remove/<int:producto_id>/', views.cliente_remove_from_cart, name='cliente_remove_from_cart'),
    
    # URL para la página de checkout del cliente
    path('cliente/checkout/', views.cliente_checkout, name='cliente_checkout'),


    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    
    # Tu exportación de ventas ACTUAL
    path('exportar-excel/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
    
    # --- AÑADE ESTA LÍNEA ---
    path('exportar/rentabilidad/', views.exportar_reporte_rentabilidad, name='exportar_reporte_rentabilidad'),
]