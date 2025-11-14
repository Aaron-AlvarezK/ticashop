from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Proveedor
from .forms import ProveedorForm


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