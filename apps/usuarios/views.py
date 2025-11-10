from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import CrearUsuarioForm
from .models import *
from django.utils import timezone
from apps.usuarios.models import Usuario
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.ventas.models import Pedido

@login_required
def dashboard(request):
    usuario = request.user
    context = {
        'usuario': usuario,
    }
    
    # Redirección según rol
    if usuario.rol == 'Administrador':
        return render(request, 'dashboard/admin_dashboard.html', context)
    elif usuario.rol == 'Vendedor':
        return render(request, 'dashboard/vendedor_dashboard.html', context)
    elif usuario.rol == 'Tesoreria':
        return render(request, 'dashboard/tesoreria_dashboard.html', context)
    elif usuario.rol == 'Cliente':
        return render(request, 'dashboard/cliente_dashboard.html', context)
    else:
        messages.error(request, 'Rol no reconocido')
        return redirect('login')

def custom_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

def es_administrador(user):
    return user.is_authenticated and user.rol == 'Administrador'

@user_passes_test(es_administrador)
def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('dashboard')
    else:
        form = CrearUsuarioForm()
    
    return render(request, 'usuarios/crear_usuario.html', {'form': form})

@user_passes_test(es_administrador)
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios})


@user_passes_test(es_administrador)
def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('listar_usuarios')
    else:
        form = CrearUsuarioForm()
    return render(request, 'usuarios/crear_usuario.html', {'form': form})


@user_passes_test(es_administrador)
def editar_usuario(request, user_id):
    usuario = Usuario.objects.get(id=user_id)
    form = CrearUsuarioForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('listar_usuarios')
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})


@user_passes_test(es_administrador)
def eliminar_usuario(request, user_id):
    usuario = Usuario.objects.get(id=user_id)
    usuario.delete()
    messages.success(request, 'Usuario eliminado correctamente.')
    return redirect('listar_usuarios')

from .forms import CrearUsuarioForm, EditarUsuarioForm

@user_passes_test(es_administrador)
def editar_usuario(request, user_id):
    usuario = Usuario.objects.get(id=user_id)
    form = EditarUsuarioForm(request.POST or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('listar_usuarios')
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
def dashboard(request):
    usuario = request.user
    
    # Estadísticas
    total_usuarios = Usuario.objects.count()
    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.count()
    
    # Pedidos de hoy
    hoy = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=hoy).count()
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.objects.filter(
        stock__lte=models.F('stock_minimo'),
        activo=True
    ).order_by('stock')[:10]
    
    context = {
        'usuario': usuario,
        'total_usuarios': total_usuarios,
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'pedidos_hoy': pedidos_hoy,
        'productos_stock_bajo': productos_stock_bajo,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)