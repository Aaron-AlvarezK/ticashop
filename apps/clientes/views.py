from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Proveedor
from .forms import ProveedorForm, ClienteForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Proveedor, Cliente # <-- Asegúrate de importar Cliente
from .forms import ProveedorForm, ClienteForm, CompletarPerfilForm # <-- Importa el nuevo form

def es_administrador(usuario):
    return usuario.rol == 'Administrador'

@login_required
def listar_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'clientes/listar_proveedores.html', {'proveedores': proveedores})

@login_required
@user_passes_test(es_administrador)
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Proveedor creado correctamente.')
            return redirect('clientes:listar_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'clientes/crear_proveedor.html', {'form': form})

@login_required
@user_passes_test(es_administrador)
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Proveedor actualizado correctamente.')
            return redirect('clientes:listar_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'clientes/editar_proveedor.html', {'form': form})

@login_required
@user_passes_test(es_administrador)
def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    proveedor.delete()
    messages.success(request, '🗑️ Proveedor eliminado correctamente.')
    return redirect('clientes:listar_proveedores')

@login_required
@require_POST # Esta vista solo acepta datos (POST), no se puede navegar a ella
def crear_cliente_ajax(request):
    """
    Vista especial para ser llamada por JavaScript (AJAX) desde el modal.
    Crea el cliente y devuelve sus datos en formato JSON.
    """
    form = ClienteForm(request.POST)
    if form.is_valid():
        try:
            nuevo_cliente = form.save()
            # Si se guarda bien, devolvemos los datos del nuevo cliente
            return JsonResponse({
                'success': True,
                'id': nuevo_cliente.id,
                'nombre': nuevo_cliente.razon_social,
                'rut': nuevo_cliente.rut
            })
        except Exception as e:
            # Si falla (ej. RUT duplicado)
            return JsonResponse({'success': False, 'errors': {'general': str(e)}})
    else:
        # Si el formulario no es válido
        return JsonResponse({'success': False, 'errors': form.errors.as_json()})
    

@login_required
def completar_perfil(request):
    """
    Vista para que un nuevo Cliente (Usuario con rol='Cliente')
    cree su perfil de Cliente (con RUT, dirección, etc.).
    """
    # Si el usuario ya tiene perfil, no debería estar aquí. Lo sacamos.
    if hasattr(request.user, 'perfil_cliente'):
        return redirect('usuarios:dashboard')

    if request.method == 'POST':
        form = CompletarPerfilForm(request.POST)
        if form.is_valid():
            # Guardamos el perfil PERO sin 'commitear' a la DB
            perfil = form.save(commit=False)
            # --- ¡LA MAGIA! ---
            # Asignamos el usuario actual al perfil
            perfil.user = request.user 
            perfil.save()
            
            messages.success(request, '¡Tu perfil ha sido completado! Ya puedes comprar.')
            return redirect('usuarios:dashboard') # Lo mandamos de vuelta al dashboard/tienda
    else:
        form = CompletarPerfilForm()

    return render(request, 'clientes/completar_perfil.html', {'form': form})