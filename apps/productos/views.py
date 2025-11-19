from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm, ImportCostoForm
from decimal import Decimal # Importación necesaria para manejar valores monetarios
import openpyxl # Importación necesaria para la lectura del Excel


# ========== FUNCIONES AUXILIARES ==========

def es_administrador(usuario):
    return usuario.is_authenticated and usuario.rol == 'Administrador'

def puede_ver_productos(usuario):
    return usuario.is_authenticated and usuario.rol in ['Administrador', 'Vendedor']


# ========== LISTADO Y FILTROS ==========

@login_required
@user_passes_test(puede_ver_productos)
def listar_productos(request):
    productos = Producto.objects.select_related('categoria', 'proveedor').all()

    # Filtro de búsqueda
    buscar = request.GET.get('buscar')
    if buscar:
        productos = productos.filter(nombre__icontains=buscar)

    return render(request, 'productos/listar_productos.html', {'productos': productos})


# ========== CRUD ==========

@login_required
@user_passes_test(es_administrador)
def crear_producto(request):
    """
    Crea un producto. Recibe request.FILES para la imagen.
    """
    if request.method == 'POST':
        # Pasamos request.POST (texto) Y request.FILES (imagen/archivo)
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('productos:listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_producto.html', {'form': form})


@login_required
@user_passes_test(es_administrador)
def editar_producto(request, producto_id):
    """
    Edita un producto. Recibe request.FILES para la imagen.
    """
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        # Pasamos request.POST, request.FILES y la instancia (objeto existente)
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('productos:listar_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar_producto.html', {'form': form, 'producto': producto})


@login_required
@user_passes_test(es_administrador)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente.')
    return redirect('productos:listar_productos')


# ========== IMPORTACIÓN MASIVA DE COSTOS Y PRECIOS ==========

@login_required
@user_passes_test(es_administrador)
def importar_costos_excel(request):
    """
    Vista para subir el Excel y actualizar Costos y Precios de Venta masivamente.
    El Excel espera: Columna A=CODIGO, Columna B=COSTO_NETO, Columna C=PRECIO_VENTA.
    """
    if request.method == 'POST':
        form = ImportCostoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            
            try:
                wb = openpyxl.load_workbook(archivo)
                sheet = wb.active
            except Exception as e:
                messages.error(request, f"Error al leer el archivo Excel: {e}")
                return redirect('productos:importar_costos')

            productos_actualizados = 0
            productos_no_encontrados = []
            
            # Iterar sobre las filas (desde la 2 para saltar el encabezado)
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue

                codigo_producto = str(row[0]).strip() # Columna A (Obligatoria)
                
                # Lectura segura de las columnas opcionales
                costo_neto = row[1] if len(row) > 1 else None      # Columna B
                precio_venta = row[2] if len(row) > 2 else None    # Columna C

                try:
                    producto = Producto.objects.get(codigo=codigo_producto)
                    cambios = False

                    # 1. Actualizar Costo (si viene)
                    if costo_neto is not None:
                        try:
                            producto.costo_unitario = Decimal(str(costo_neto))
                            cambios = True
                        except:
                            pass 

                    # 2. Actualizar Precio Venta (si viene)
                    if precio_venta is not None:
                        try:
                            producto.precio_unitario = Decimal(str(precio_venta))
                            cambios = True
                        except:
                            pass 

                    if cambios:
                        producto.save()
                        productos_actualizados += 1
                    
                except Producto.DoesNotExist:
                    productos_no_encontrados.append(codigo_producto)
                except Exception as e:
                    messages.error(request, f"Error en fila {codigo_producto}: {e}")

            messages.success(request, f"✅ Proceso completado. {productos_actualizados} productos actualizados.")
            if productos_no_encontrados:
                messages.warning(request, f"⚠️ SKU no encontrados: {', '.join(productos_no_encontrados)}")
            
            return redirect('productos:listar_productos')

    else:
        form = ImportCostoForm()

    return render(request, 'productos/importar_costos.html', {'form': form})