from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from .models import Pedido, DetallePedido
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from .forms import PedidoForm, DetallePedidoForm

def puede_gestionar_pedidos(usuario):
    return usuario.is_authenticated and usuario.rol in ['Administrador', 'Vendedor']

@login_required
@user_passes_test(puede_gestionar_pedidos)
def listar_pedidos(request):
    pedidos = Pedido.objects.select_related('cliente', 'usuario').all().order_by('-fecha_creacion')
    return render(request, 'ventas/listar_pedidos.html', {'pedidos': pedidos})


@login_required
@user_passes_test(puede_gestionar_pedidos)
def crear_pedido(request):
    # 🔥 Validar que haya productos disponibles
    productos_disponibles = Producto.objects.filter(activo=True, stock__gt=0)
    
    if not productos_disponibles.exists():
        messages.error(request, '❌ No hay productos disponibles para crear un pedido. Por favor, agregue productos con stock primero.')
        return redirect('listar_pedidos')
    
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.usuario = request.user
            pedido.save()
            messages.success(request, f'Pedido #{pedido.id} creado exitosamente.')
            return redirect('agregar_productos_pedido', pedido_id=pedido.id)
    else:
        form = PedidoForm()
    
    return render(request, 'ventas/crear_pedido.html', {'form': form})


@login_required
@user_passes_test(puede_gestionar_pedidos)
def agregar_productos_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # 🔥 Solo productos activos con stock disponible
    productos_disponibles = Producto.objects.filter(activo=True, stock__gt=0).order_by('nombre')
    
    if not productos_disponibles.exists():
        messages.error(request, '❌ No hay productos disponibles con stock.')
        return redirect('listar_pedidos')
    
    detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = int(request.POST.get('cantidad', 0))
        
        if producto_id and cantidad > 0:
            producto = get_object_or_404(Producto, id=producto_id)
            
            # 🔥 Validar stock disponible
            if cantidad > producto.stock:
                messages.error(request, f'❌ Stock insuficiente. Solo hay {producto.stock} unidades disponibles de {producto.nombre}.')
                return redirect('agregar_productos_pedido', pedido_id=pedido.id)
            
            # Verificar si el producto ya está en el pedido
            detalle_existente = DetallePedido.objects.filter(pedido=pedido, producto=producto).first()
            
            if detalle_existente:
                # Validar que la suma no exceda el stock
                nueva_cantidad = detalle_existente.cantidad + cantidad
                if nueva_cantidad > producto.stock:
                    messages.error(request, f'❌ Stock insuficiente. Solo hay {producto.stock} unidades disponibles de {producto.nombre}.')
                    return redirect('agregar_productos_pedido', pedido_id=pedido.id)
                
                detalle_existente.cantidad = nueva_cantidad
                detalle_existente.subtotal = detalle_existente.cantidad * detalle_existente.precio_unitario_venta  # 🔥 Cambio aquí
                detalle_existente.save()
                messages.success(request, f'✅ Cantidad actualizada: {producto.nombre}')
            else:
                # Crear nuevo detalle
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_venta=producto.precio_unitario,  # 🔥 Cambio aquí
                    subtotal=cantidad * producto.precio_unitario
                )
                messages.success(request, f'✅ Producto agregado: {producto.nombre}')
            
            # Actualizar total del pedido
            pedido.calcular_total()
            
            return redirect('agregar_productos_pedido', pedido_id=pedido.id)
    
    context = {
        'pedido': pedido,
        'productos': productos_disponibles,
        'detalles': detalles,
    }
    
    return render(request, 'ventas/agregar_productos_pedido.html', context)


@login_required
@user_passes_test(puede_gestionar_pedidos)
def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Validar que el pedido tenga productos
    if not pedido.detalles.exists():
        messages.error(request, '❌ No se puede confirmar un pedido sin productos.')
        return redirect('agregar_productos_pedido', pedido_id=pedido.id)
    
    # 🔥 Descontar stock de cada producto
    with transaction.atomic():
        for detalle in pedido.detalles.all():
            producto = detalle.producto
            
            # Validar stock nuevamente antes de confirmar
            if detalle.cantidad > producto.stock:
                messages.error(request, f'❌ Stock insuficiente para {producto.nombre}. Solo hay {producto.stock} unidades.')
                return redirect('agregar_productos_pedido', pedido_id=pedido.id)
            
            # Descontar stock
            producto.stock -= detalle.cantidad
            producto.save()
        
        # Cambiar estado del pedido
        pedido.estado = 'Procesando'  # 🔥 Cambié a 'Procesando' porque 'Confirmado' no existe en tus opciones
        pedido.save()
    
    messages.success(request, f'✅ Pedido #{pedido.id} confirmado exitosamente. Stock actualizado.')
    return redirect('listar_pedidos')


@login_required
@user_passes_test(puede_gestionar_pedidos)
def eliminar_producto_pedido(request, detalle_id):
    detalle = get_object_or_404(DetallePedido, id=detalle_id)
    pedido = detalle.pedido
    detalle.delete()
    
    # El total se actualiza automáticamente en el método delete() del modelo
    
    messages.success(request, '✅ Producto eliminado del pedido.')
    return redirect('agregar_productos_pedido', pedido_id=pedido.id)


@login_required
@user_passes_test(puede_gestionar_pedidos)
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')

    context = {
        'pedido': pedido,
        'detalles': detalles,
    }

    return render(request, 'ventas/detalle_pedido.html', context)