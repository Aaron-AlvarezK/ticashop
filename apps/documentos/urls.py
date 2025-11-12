from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_documentos, name='listar_documentos'),
    path('crear-desde-pedido/<int:pedido_id>/', views.crear_documento_desde_pedido, name='crear_documento_desde_pedido'),
    path('detalle/<int:documento_id>/', views.detalle_documento, name='detalle_documento'),
    path('registrar-pago/<int:documento_id>/', views.registrar_pago, name='registrar_pago'),
    path('anular/<int:documento_id>/', views.anular_documento, name='anular_documento'),
]