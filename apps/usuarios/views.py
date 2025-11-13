from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.db import models
from django.utils import timezone
from datetime import date

from .models import Usuario
from .forms import CrearUsuarioForm, EditarUsuarioForm
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.ventas.models import Pedido


# ========== FUNCIÓN AUXILIAR ==========
def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.rol == 'Administrador'


# ========== DASHBOARD PRINCIPAL ==========
@login_required
def dashboard(request):
    usuario = request.user
    rol = usuario.rol.strip() if usuario.rol else ''

    # --- Panel de ADMINISTRADOR ---
    if rol == 'Administrador':
        total_usuarios = Usuario.objects.count()
        total_clientes = Cliente.objects.count()
        total_productos = Producto.objects.count()
        pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=date.today()).count()
        
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

    # --- Panel de VENDEDOR ---
    elif rol == 'Vendedor':
        total_clientes = Cliente.objects.count()
        total_productos = Producto.objects.filter(activo=True).count()
        pedidos_hoy = Pedido.objects.filter(
            usuario=usuario, 
            fecha_creacion__date=date.today()
        ).count()
        
        # Total de pedidos del vendedor
        mis_pedidos = Pedido.objects.filter(usuario=usuario).count()

        context = {
            'usuario': usuario,
            'total_clientes': total_clientes,
            'total_productos': total_productos,
            'pedidos_hoy': pedidos_hoy,
            'mis_pedidos': mis_pedidos,
        }
        return render(request, 'dashboard/vendedor_dashboard.html', context)
    
    # --- Panel de TESORERÍA (opcional) ---
    elif rol == 'Tesorería':
        total_pedidos = Pedido.objects.count()
        pedidos_pendientes = Pedido.objects.filter(estado='Pendiente').count()
        pedidos_completados = Pedido.objects.filter(estado='Completado').count()
        
        context = {
            'usuario': usuario,
            'total_pedidos': total_pedidos,
            'pedidos_pendientes': pedidos_pendientes,
            'pedidos_completados': pedidos_completados,
        }
        return render(request, 'dashboard/tesoreria_dashboard.html', context)

    # Si no tiene rol válido
    return redirect('login')


# ========== LOGOUT PERSONALIZADO ==========
def custom_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# ========== CRUD DE USUARIOS (solo admin) ==========
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
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('listar_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)
    
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})


@user_passes_test(es_administrador)
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('listar_usuarios')
    
    return render(request, 'usuarios/confirmar_eliminar.html', {'usuario': usuario})