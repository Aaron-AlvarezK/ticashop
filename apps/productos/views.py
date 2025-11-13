from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm

def es_administrador(usuario):
    return usuario.is_authenticated and usuario.rol == 'Administrador'

def puede_ver_productos(usuario):
    return usuario.is_authenticated and usuario.rol in ['Administrador', 'Vendedor']

@login_required
@user_passes_test(puede_ver_productos)
def listar_productos(request):
    productos = Producto.objects.select_related('categoria', 'proveedor').all()

    # Filtro de búsqueda
    buscar = request.GET.get('buscar')
    if buscar:
        productos = productos.filter(nombre__icontains=buscar)

    return render(request, 'productos/listar_productos.html', {'productos': productos})


@login_required
@user_passes_test(es_administrador)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_producto.html', {'form': form})


@login_required
@user_passes_test(es_administrador)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('listar_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar_producto.html', {'form': form, 'producto': producto})


@login_required
@user_passes_test(es_administrador)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente.')
    return redirect('listar_productos')