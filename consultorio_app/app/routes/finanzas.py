"""
Rutas para el módulo de finanzas.
Solo accesible para usuarios con rol DUEÑA.
"""
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps

from app.forms import GastoForm
from app.services.gasto.crear_gasto_service import CrearGastoService
from app.services.gasto.listar_gastos_service import ListarGastosService
from app.services.gasto.obtener_estadisticas_finanzas_service import ObtenerEstadisticasFinanzasService
from app.services.common.exceptions import OdontoAppError
from app.models import ObraSocial, Paciente

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/finanzas')


def _cargar_pacientes_en_form(form: GastoForm):
    """Carga opciones de pacientes para el formulario de gastos."""
    pacientes = Paciente.query.order_by(Paciente.apellido.asc(), Paciente.nombre.asc()).all()
    form.paciente_id.choices = [(0, 'Sin paciente')] + [
        (p.id, f'{p.apellido}, {p.nombre}')
        for p in pacientes
    ]


def _obtener_mapa_pacientes_desde_gastos(gastos_lista):
    """Construye un mapa id->paciente con los ids embebidos en observaciones."""
    paciente_ids = set()
    for gasto in gastos_lista:
        paciente_id = CrearGastoService.extraer_paciente_id(gasto.observaciones)
        if paciente_id:
            paciente_ids.add(paciente_id)

    if not paciente_ids:
        return {}

    pacientes = Paciente.query.filter(Paciente.id.in_(paciente_ids)).all()
    return {p.id: p for p in pacientes}


def duena_required(f):
    """Decorador para requerir rol DUEÑA."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('main.login'))
        
        if not current_user.tiene_acceso_finanzas():
            flash('No tiene permisos para acceder a finanzas', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


@finanzas_bp.route('/dashboard')
@login_required
@duena_required
def dashboard():
    """Dashboard principal de finanzas."""
    # Obtener período seleccionado
    periodo = request.args.get('periodo', 'mes')
    obra_social = request.args.get('obra_social')
    
    # Calcular fechas según período
    hoy = date.today()
    
    if periodo == 'semana':
        fecha_desde = hoy - timedelta(days=7)
        fecha_hasta = hoy
        titulo_periodo = 'Última Semana'
    elif periodo == 'mes':
        fecha_desde = date(hoy.year, hoy.month, 1)
        fecha_hasta = hoy
        titulo_periodo = 'Este Mes'
    elif periodo == 'anio':
        fecha_desde = date(hoy.year, 1, 1)
        fecha_hasta = hoy
        titulo_periodo = 'Este Año'
    else:
        # Personalizado
        fecha_desde_str = request.args.get('fecha_desde')
        fecha_hasta_str = request.args.get('fecha_hasta')
        
        if fecha_desde_str and fecha_hasta_str:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            titulo_periodo = f'{fecha_desde.strftime("%d/%m/%Y")} - {fecha_hasta.strftime("%d/%m/%Y")}'
        else:
            fecha_desde = date(hoy.year, hoy.month, 1)
            fecha_hasta = hoy
            titulo_periodo = 'Este Mes'
    
    # Obtener resumen financiero
    resumen = ObtenerEstadisticasFinanzasService.obtener_resumen(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Opciones de obra social (agregamos "Todo" y evitamos duplicados ajenos a la base)
    obras_sociales_db = [os.nombre for os in ObraSocial.query.order_by(ObraSocial.nombre).all()]
    obras_sociales_opciones = ['Todo', 'Particular', 'IPSS']

    for nombre in obras_sociales_db:
        if nombre and nombre not in obras_sociales_opciones:
            obras_sociales_opciones.append(nombre)

    # Seleccionar obra social por defecto si no viene en la request o no es válida
    if not obra_social or obra_social not in obras_sociales_opciones:
        obra_social = 'Todo'

    # Obtener desglose por práctica para la obra social elegida
    ingresos_por_practica = ObtenerEstadisticasFinanzasService.obtener_ingresos_por_practica(
        obra_social=obra_social,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Obtener resumen por fuente de pago (para las tarjetas superiores)
    ingresos_por_fuente = ObtenerEstadisticasFinanzasService.obtener_ingresos_por_tipo(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Obtener detalle de prestaciones si se seleccionó una obra social específica
    detalle_prestaciones = []
    if obra_social and obra_social.lower() not in ('todas', 'todo'):
        detalle_prestaciones = ObtenerEstadisticasFinanzasService.obtener_detalle_prestaciones(
            obra_social=obra_social,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=100
        )
    
    # Obtener desglose por categoría de gastos
    egresos_por_categoria = ObtenerEstadisticasFinanzasService.obtener_egresos_por_categoria(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    return render_template(
        'finanzas/dashboard.html',
        resumen=resumen,
        ingresos_por_practica=ingresos_por_practica,
        ingresos_por_fuente=ingresos_por_fuente,
        detalle_prestaciones=detalle_prestaciones,
        egresos_por_categoria=egresos_por_categoria,
        periodo=periodo,
        titulo_periodo=titulo_periodo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        obra_social=obra_social,
        obras_sociales_opciones=obras_sociales_opciones,
    )


@finanzas_bp.route('/gastos')
@login_required
@duena_required
def gastos():
    """Lista de gastos."""
    # Obtener filtros
    fecha_desde_str = request.args.get('fecha_desde')
    fecha_hasta_str = request.args.get('fecha_hasta')
    categoria = request.args.get('categoria')
    
    fecha_desde = None
    fecha_hasta = None
    
    if fecha_desde_str:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
    
    if fecha_hasta_str:
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
    
    # Listar gastos
    gastos_lista = ListarGastosService.listar(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categoria=categoria
    )

    pacientes_por_id = _obtener_mapa_pacientes_desde_gastos(gastos_lista)
    for gasto in gastos_lista:
        paciente_id = CrearGastoService.extraer_paciente_id(gasto.observaciones)
        paciente = pacientes_por_id.get(paciente_id)
        gasto.paciente_relacionado = paciente
        gasto.observaciones_limpias = CrearGastoService.limpiar_observaciones(gasto.observaciones)
    
    # Categorías disponibles
    categorias = ['INSUMO', 'OPERATIVO', 'CURSO', 'EJERCICIO_PROFESIONAL', 'TECNICO_PROTESIS', 'OTROS']
    
    return render_template(
        'finanzas/gastos.html',
        gastos=gastos_lista,
        categorias=categorias,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categoria_seleccionada=categoria
    )


@finanzas_bp.route('/gastos/nuevo', methods=['GET', 'POST'])
@login_required
@duena_required
def nuevo_gasto():
    """Crear nuevo gasto con validación WTF."""
    form = GastoForm()
    _cargar_pacientes_en_form(form)
    
    if form.validate_on_submit():
        try:
            # Los datos ya están validados por WTF
            gasto = CrearGastoService.crear(
                descripcion=form.descripcion.data,
                monto=form.monto.data,
                fecha=form.fecha.data,
                categoria=form.categoria.data,
                creado_por_id=current_user.id,
                observaciones=form.observaciones.data or None,
                paciente_id=(form.paciente_id.data or None) if form.paciente_id.data != 0 else None,
            )
            
            flash(f'Gasto "{gasto.descripcion}" creado exitosamente', 'success')
            return redirect(url_for('finanzas.gastos'))
            
        except OdontoAppError as e:
            flash(f'Error: {e.mensaje}', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {str(e)}', 'danger')
    
    return render_template('finanzas/nuevo_gasto.html', form=form, es_edicion=False)


@finanzas_bp.route('/gastos/<int:gasto_id>/editar', methods=['GET', 'POST'])
@login_required
@duena_required
def editar_gasto(gasto_id):
    """Permite editar un gasto existente."""
    gasto = ListarGastosService.obtener_por_id(gasto_id)
    if not gasto:
        flash('Gasto no encontrado', 'danger')
        return redirect(url_for('finanzas.gastos'))

    form = GastoForm(obj=gasto)
    _cargar_pacientes_en_form(form)

    if request.method == 'GET':
        paciente_id = CrearGastoService.extraer_paciente_id(gasto.observaciones) or 0
        form.paciente_id.data = paciente_id
        form.observaciones.data = CrearGastoService.limpiar_observaciones(gasto.observaciones)

    if form.validate_on_submit():
        try:
            gasto_actualizado = CrearGastoService.actualizar(
                gasto_id=gasto.id,
                descripcion=form.descripcion.data,
                monto=form.monto.data,
                fecha=form.fecha.data,
                categoria=form.categoria.data,
                observaciones=form.observaciones.data or None,
                paciente_id=(form.paciente_id.data or None) if form.paciente_id.data != 0 else None,
            )
            flash(f'Gasto "{gasto_actualizado.descripcion}" actualizado exitosamente', 'success')
            return redirect(url_for('finanzas.gastos'))
        except OdontoAppError as e:
            flash(f'Error: {e.mensaje}', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {str(e)}', 'danger')

    return render_template('finanzas/nuevo_gasto.html', form=form, es_edicion=True, gasto=gasto)


@finanzas_bp.route('/reportes')
@login_required
@duena_required
def reportes():
    """Reportes financieros anuales."""
    # Obtener año seleccionado
    anio = request.args.get('anio', type=int, default=date.today().year)
    
    # Obtener evolución mensual
    evolucion = ObtenerEstadisticasFinanzasService.obtener_evolucion_mensual(anio)
    
    return render_template(
        'finanzas/reportes.html',
        evolucion=evolucion,
        anio_seleccionado=anio,
        anio_actual=date.today().year
    )


@finanzas_bp.route('/api/resumen')
@login_required
@duena_required
def api_resumen():
    """API para obtener resumen financiero (para gráficos)."""
    fecha_desde_str = request.args.get('fecha_desde')
    fecha_hasta_str = request.args.get('fecha_hasta')
    paciente_id = request.args.get('paciente_id', type=int)
    
    fecha_desde = None
    fecha_hasta = None
    
    if fecha_desde_str:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
    
    if fecha_hasta_str:
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
    
    resumen = ObtenerEstadisticasFinanzasService.obtener_resumen(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        paciente_id=paciente_id
    )
    
    return jsonify(resumen)
