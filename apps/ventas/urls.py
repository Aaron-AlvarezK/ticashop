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
    # Paso 1: Datos del pedido y del documento
    path('pedidos/nuevo/', views.crear_pedido_datos, name='crear_pedido_datos'),

    # Paso 2: Agregar productos y confirmar
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
]