from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_documentos, name='listar_documentos'),
    path('detalle/<int:documento_id>/', views.detalle_documento, name='detalle_documento'),
]