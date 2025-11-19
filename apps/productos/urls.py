from django.urls import path
from . import views

app_name = 'productos'
urlpatterns = [
    path('', views.listar_productos, name='listar_productos'),
    path('nuevo/', views.crear_producto, name='crear_producto'),
    path('editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('importar-costos/', views.importar_costos_excel, name='importar_costos'),
]