from django.urls import path
from . import views

urlpatterns = [
    path('pedidos/', views.listar_pedidos, name='listar_pedidos'),
    path('pedidos/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/agregar-productos/', views.agregar_productos_pedido, name='agregar_productos_pedido'),
    path('pedidos/<int:pedido_id>/confirmar/', views.confirmar_pedido, name='confirmar_pedido'),
    path('pedidos/detalle/<int:detalle_id>/eliminar/', views.eliminar_producto_pedido, name='eliminar_producto_pedido'),
]