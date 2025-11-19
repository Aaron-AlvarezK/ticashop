from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- LÍNEA CORREGIDA ---
    # Ahora, la página de inicio '/' redirige a la tienda pública.
    path('', RedirectView.as_view(url='/usuarios/dashboard/', permanent=False)), 
    
    path('clientes/', include('apps.clientes.urls')),  
    path('usuarios/', include('apps.usuarios.urls')),
    path('ventas/', include('apps.ventas.urls')),
    path('productos/', include('apps.productos.urls')),
    path('documentos/', include('apps.documentos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)