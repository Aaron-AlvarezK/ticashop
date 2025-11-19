from django.urls import path
from . import views
app_name = 'documentos'

urlpatterns = [
    path('', views.listar_documentos, name='listar_documentos'),
    path('documento/<int:documento_id>/', views.detalle_documento, name='detalle_documento'),
    path('documento/<int:factura_id>/nota-credito/crear/', views.crear_nota_credito, name='crear_nota_credito'),
    path('nota-credito/<int:nota_id>/', views.detalle_nota_credito, name='detalle_nota_credito'), 
]