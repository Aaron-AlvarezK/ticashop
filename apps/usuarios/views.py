from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.db import models
from django.utils import timezone
from datetime import date

from .models import Usuario
from .forms import CrearUsuarioForm, EditarUsuarioForm, ClienteRegistrationForm
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.ventas.models import Pedido
from apps.documentos.models import DocumentoVenta
from datetime import timedelta
# ========== FUNCIÓN AUXILIAR ==========
def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.rol == 'Administrador'


# ========== DASHBOARD PRINCIPAL (HECHO PÚBLICO) ==========
# ¡Quitamos @login_required de aquí!
def dashboard(request):
    
    # --- 1. LÓGICA PARA INVITADOS (NO AUTENTICADOS) ---
    if not request.user.is_authenticated:
        # Es un visitante, le mostramos la tienda.
        total_productos = Producto.objects.filter(activo=True).count()
        productos = Producto.objects.filter(activo=True)
        
        context = {
            'usuario': request.user, # Será 'AnonymousUser'
            'total_productos': total_productos,
            'productos': productos,
        }
        return render(request, 'dashboard/cliente_dashboard.html', context)

    # --- 2. LÓGICA PARA USUARIOS AUTENTICADOS ---
    # Si llegamos aquí, el usuario SÍ está logueado.
    usuario = request.user
    rol = usuario.rol.strip() if usuario.rol else ''

    # --- Panel de ADMINISTRADOR ---
    if rol == 'Administrador':
        total_usuarios = Usuario.objects.count()
        total_clientes = Cliente.objects.count()
        total_productos = Producto.objects.count()
        pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=date.today()).count()

        productos_stock_bajo = Producto.objects.filter(
            stock__lte=models.F('stock_minimo'),
            activo=True
        ).order_by('stock')[:10]

        pedidos_devuelta = Pedido.objects.filter(documentoventa__estado='Devuelta').count()
        pedidos_devuelta_parcial = Pedido.objects.filter(documentoventa__estado='Devuelta Parcial').count()

        context = {
            'usuario': usuario,
            'total_usuarios': total_usuarios,
            'total_clientes': total_clientes,
            'total_productos': total_productos,
            'pedidos_hoy': pedidos_hoy,
            'productos_stock_bajo': productos_stock_bajo,
            'pedidos_devuelta': pedidos_devuelta,
            'pedidos_devuelta_parcial': pedidos_devuelta_parcial,
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
    elif rol == 'Tesoreria': # Ya corregimos el acento en el paso anterior
        hoy = timezone.localdate()

        # Conteo de Pedidos (usando la lógica existente)
        total_pedidos = Pedido.objects.count()
        pedidos_pendientes = Pedido.objects.filter(estado='Pendiente').count()
        pedidos_completados = Pedido.objects.filter(estado='Completado').count()
        
        # 1. Alertas de Facturas Vencidas (Busca las que estén EMITIDAS/PAGO PARCIAL Y vencidas)
        facturas_vencidas = DocumentoVenta.objects.filter(
            estado__in=['Emitida', 'Pago Parcial'],
            fecha_vencimiento__lt=hoy
        )
        
        # 2. Alertas de Facturas Por Vencer (Ej: en los próximos 7 días)
        fecha_limite_futura = hoy + timedelta(days=7)
        facturas_por_vencer = DocumentoVenta.objects.filter(
            estado__in=['Emitida', 'Pago Parcial'],
            fecha_vencimiento__range=[hoy, fecha_limite_futura]
        )

        context = {
            'usuario': usuario,
            'total_pedidos': total_pedidos,
            'pedidos_pendientes': pedidos_pendientes,
            'pedidos_completados': pedidos_completados,
            'facturas_vencidas': facturas_vencidas, # <-- Nuevo para el template
            'facturas_por_vencer': facturas_por_vencer, # <-- Nuevo para el template
        }
        return render(request, 'dashboard/tesoreria_dashboard.html', context)
    
    # --- Panel de CLIENTE ---
    elif rol == 'Cliente':
        # (Ya quitamos la redirección a 'completar_perfil' de aquí)
        total_productos = Producto.objects.filter(activo=True).count()
        productos = Producto.objects.filter(activo=True)
        
        context = {
            'usuario': usuario,
            'total_productos': total_productos,
            'productos': productos,
        }
        return render(request, 'dashboard/cliente_dashboard.html', context)

    # Si tiene rol inválido (pero está logueado)
    return redirect('usuarios:login')


# ========== LOGOUT PERSONALIZADO ==========
def custom_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('usuarios:login')


# ========== VISTA DE REGISTRO (NUEVA) ==========
def registro_cliente(request):
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada con éxito! Ya puedes iniciar sesión.')
            return redirect('usuarios:login')
        else:
            pass
    else:
        form = ClienteRegistrationForm()
    
    return render(request, 'registration/registro_cliente.html', {'form': form})


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
            return redirect('usuarios:listar_usuarios')
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
            return redirect('usuarios:listar_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)
    
    return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})


@user_passes_test(es_administrador)
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('usuarios:listar_usuarios')
    
    return render(request, 'usuarios/confirmar_eliminar.html', {'usuario': usuario})