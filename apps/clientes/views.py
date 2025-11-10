from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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