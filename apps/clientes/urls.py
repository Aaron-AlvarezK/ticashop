from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'clientes'
urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
        
    # 🔥 CRUD de Proveedores
    path('proveedores/', views.listar_proveedores, name='listar_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    path('ajax/crear-cliente/', views.crear_cliente_ajax, name='crear_cliente_ajax'),

    path('completar-perfil/', views.completar_perfil, name='completar_perfil'),
]