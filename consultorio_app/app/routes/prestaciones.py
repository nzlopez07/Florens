from datetime import datetime
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.forms import PrestacionForm
from app.models import Prestacion
from app.services.prestacion import (
    ListarPrestacionesService,
    CrearPrestacionService,
    ActualizarPrestacionService,
    EliminarPrestacionService,
    RegistrarAutorizacionPrestacionService,
    RegistrarCobroPrestacionService,
    RegistrarRealizacionPrestacionService,
    MarcarItemRealizadoService,
)
from app.services.paciente import BuscarPacientesService
from app.services.practica import ListarPracticasService
from app.services.common import (
    PacienteNoEncontradoError,
    PracticaNoEncontradaError,
    DatosInvalidosError,
    OdontoAppError,
    EstadoPrestacionInvalidoError,
    PrestacionNoAutorizadaError,
    FechasRealizacionInvalidasError,
)
from . import main_bp


def _extraer_practicas_form():
    """Obtiene prácticas y cantidades desde el formulario JS."""
    practica_ids = request.form.getlist('practica_ids[]', type=int)
    practica_cantidades = request.form.getlist('practica_cantidades[]', type=int)

    if not practica_ids:
        return [], practica_ids, practica_cantidades, 'Debe seleccionar al menos una práctica'

    if len(practica_cantidades) != len(practica_ids):
        return [], practica_ids, practica_cantidades, 'Las cantidades de las prácticas no son válidas'

    practicas_data = []
    for practica_id, cantidad in zip(practica_ids, practica_cantidades):
        cantidad_segura = max(1, int(cantidad) if cantidad is not None else 1)
        practicas_data.append({'id': practica_id, 'cantidad': cantidad_segura})

    return practicas_data, practica_ids, practica_cantidades, None


@main_bp.route('/prestaciones')
@login_required
def listar_prestaciones():
    prestaciones = ListarPrestacionesService.listar_todas()
    return render_template('prestaciones/lista.html', prestaciones=prestaciones)


@main_bp.route('/pacientes/<int:paciente_id>/prestaciones')
@login_required
def listar_prestaciones_paciente(paciente_id: int):
    try:
        paciente = BuscarPacientesService.obtener_por_id(paciente_id)
    except PacienteNoEncontradoError:
        flash('Paciente no encontrado', 'error')
        return redirect(url_for('main.listar_pacientes'))

    pagina = request.args.get('pagina', 1, type=int)

    descripcion = request.args.get('descripcion', '').strip() or None
    monto_min_str = request.args.get('monto_min', '').strip()
    monto_max_str = request.args.get('monto_max', '').strip()
    monto_min = float(monto_min_str) if monto_min_str else None
    monto_max = float(monto_max_str) if monto_max_str else None

    datos_paginacion = ListarPrestacionesService.listar_por_paciente(
        paciente_id=paciente_id,
        pagina=pagina,
        por_pagina=10,
        descripcion=descripcion,
        monto_min=monto_min,
        monto_max=monto_max,
    )

    return render_template(
        'prestaciones/paciente_lista.html',
        paciente=paciente,
        prestaciones=datos_paginacion['items'],
        pagina_actual=datos_paginacion['pagina_actual'],
        total_paginas=datos_paginacion['total_paginas'],
        total=datos_paginacion['total'],
        filtros=datos_paginacion['filtros_aplicados'],
    )


@main_bp.route('/prestaciones/nueva', methods=['GET', 'POST'])
@login_required
def nueva_prestacion():
    """Crear nueva prestación con validación WTF."""
    form = PrestacionForm()

    form.paciente_id.choices = [
        (0, '--- Seleccionar ---'),
        *[(p.id, f'{p.nombre} {p.apellido} (DNI: {p.dni})') for p in BuscarPacientesService.listar_todos()]
    ]

    paciente_id_url = request.args.get('paciente_id', type=int)
    if paciente_id_url and request.method == 'GET':
        form.paciente_id.data = paciente_id_url

    if form.validate_on_submit():
        practicas_data, practica_ids, practica_cantidades, practicas_error = _extraer_practicas_form()
        if practicas_error:
            flash(practicas_error, 'warning')
            return render_template(
                'prestaciones/nueva.html',
                form=form,
                modo_edicion=False,
                prestacion_edit_id=None,
                practica_ids_str=','.join(str(pid) for pid in practica_ids),
                practica_cantidades_str=','.join(str(cant) for cant in practica_cantidades),
            )

        try:
            monto_str = form.monto.data or '0'
            try:
                monto = Decimal(str(monto_str))
            except Exception:
                monto = Decimal('0')

            observaciones = form.observaciones.data
            if observaciones and isinstance(observaciones, str):
                observaciones = observaciones.strip() or None
            else:
                observaciones = None

            prestacion = CrearPrestacionService.execute({
                'paciente_id': form.paciente_id.data,
                'descripcion': form.descripcion.data,
                'observaciones': observaciones,
                'practicas': practicas_data,
                'descuento_porcentaje': float(form.descuento_porcentaje.data or 0),
                'descuento_fijo': float(form.descuento_fijo.data or 0),
            })
            flash('Prestación registrada exitosamente', 'success')
            return redirect(url_for('main.ver_paciente', id=form.paciente_id.data))
        except (PacienteNoEncontradoError, PracticaNoEncontradaError, DatosInvalidosError) as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar prestación: {str(e)}', 'error')

        return render_template(
            'prestaciones/nueva.html',
            form=form,
            modo_edicion=False,
            prestacion_edit_id=None,
            practica_ids_str=','.join(str(pid) for pid in practica_ids),
            practica_cantidades_str=','.join(str(cant) for cant in practica_cantidades),
        )

    return render_template(
        'prestaciones/nueva.html',
        form=form,
        modo_edicion=False,
        prestacion_edit_id=None,
        practica_ids_str='',
        practica_cantidades_str='',
    )


@main_bp.route('/prestaciones/<int:prestacion_id>', methods=['GET'])
@login_required
def ver_prestacion(prestacion_id: int):
    """Ver detalles de una prestación y permitir autorizar, cobrar, realizar."""
    prestacion = db.session.query(Prestacion).filter(
        Prestacion.id == prestacion_id
    ).first()
    
    if not prestacion:
        flash('Prestación no encontrada', 'error')
        return redirect(url_for('main.listar_prestaciones'))
    
    return render_template(
        'prestaciones/detalle.html',
        prestacion=prestacion,
    )


@main_bp.route('/prestaciones/<int:prestacion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_prestacion(prestacion_id: int):
    """Permite editar una prestación en estado borrador."""
    prestacion = db.session.query(Prestacion).filter(
        Prestacion.id == prestacion_id
    ).first()

    if not prestacion:
        flash('Prestación no encontrada', 'error')
        return redirect(url_for('main.listar_prestaciones'))

    if prestacion.estado != 'borrador':
        flash('Solo se puede editar una prestación en estado borrador', 'warning')
        return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))

    form = PrestacionForm()

    form.paciente_id.choices = [
        (0, '--- Seleccionar ---'),
        *[(p.id, f'{p.nombre} {p.apellido} (DNI: {p.dni})') for p in BuscarPacientesService.listar_todos()]
    ]

    if request.method == 'GET':
        form.prestacion_id.data = prestacion.id
        form.paciente_id.data = prestacion.paciente_id
        form.descripcion.data = prestacion.descripcion
        form.observaciones.data = prestacion.observaciones
        form.descuento_porcentaje.data = "0"
        form.descuento_fijo.data = "0"

        practica_ids = [pp.practica_id for pp in prestacion.practicas_assoc if pp.fecha_anulacion is None]
        practica_cantidades = [max(1, pp.cantidad or 1) for pp in prestacion.practicas_assoc if pp.fecha_anulacion is None]

        return render_template(
            'prestaciones/nueva.html',
            form=form,
            modo_edicion=True,
            prestacion_edit_id=prestacion.id,
            practica_ids_str=','.join(str(pid) for pid in practica_ids),
            practica_cantidades_str=','.join(str(cant) for cant in practica_cantidades),
        )

    if form.validate_on_submit():
        practicas_data, practica_ids, practica_cantidades, practicas_error = _extraer_practicas_form()
        if practicas_error:
            flash(practicas_error, 'warning')
        else:
            try:
                observaciones = form.observaciones.data
                if observaciones and isinstance(observaciones, str):
                    observaciones = observaciones.strip() or None
                else:
                    observaciones = None

                ActualizarPrestacionService.execute(
                    prestacion_id,
                    {
                        'paciente_id': form.paciente_id.data,
                        'descripcion': form.descripcion.data,
                        'observaciones': observaciones,
                        'practicas': practicas_data,
                        'descuento_porcentaje': float(form.descuento_porcentaje.data or 0),
                        'descuento_fijo': float(form.descuento_fijo.data or 0),
                    },
                )
                flash('Prestación actualizada exitosamente', 'success')
                return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))
            except (PacienteNoEncontradoError, PracticaNoEncontradaError, DatosInvalidosError, EstadoPrestacionInvalidoError) as e:
                flash(str(e), 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar prestación: {str(e)}', 'error')

        practica_ids = request.form.getlist('practica_ids[]', type=int)
        practica_cantidades = request.form.getlist('practica_cantidades[]', type=int)

        return render_template(
            'prestaciones/nueva.html',
            form=form,
            modo_edicion=True,
            prestacion_edit_id=prestacion.id,
            practica_ids_str=','.join(str(pid) for pid in practica_ids),
            practica_cantidades_str=','.join(str(cant) for cant in practica_cantidades),
        )

    # Si el form no valida, re-renderizar con datos actuales
    practica_ids = request.form.getlist('practica_ids[]', type=int)
    practica_cantidades = request.form.getlist('practica_cantidades[]', type=int)

    return render_template(
        'prestaciones/nueva.html',
        form=form,
        modo_edicion=True,
        prestacion_edit_id=prestacion.id,
        practica_ids_str=','.join(str(pid) for pid in practica_ids),
        practica_cantidades_str=','.join(str(cant) for cant in practica_cantidades),
    )


@main_bp.route('/prestaciones/<int:prestacion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_prestacion(prestacion_id: int):
    """Elimina físicamente una prestación en estado borrador."""
    prestacion = db.session.query(Prestacion).filter(
        Prestacion.id == prestacion_id
    ).first()

    paciente_id = prestacion.paciente_id if prestacion else None

    try:
        EliminarPrestacionService.execute(prestacion_id)
        flash('Prestación eliminada correctamente', 'success')
    except EstadoPrestacionInvalidoError:
        flash('Solo se pueden eliminar prestaciones en estado borrador', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la prestación: {str(e)}', 'error')

    if paciente_id:
        return redirect(url_for('main.listar_prestaciones_paciente', paciente_id=paciente_id))
    return redirect(url_for('main.listar_prestaciones'))


@main_bp.route('/prestaciones/<int:prestacion_id>/autorizar', methods=['POST'])
@login_required
def autorizar_prestacion(prestacion_id: int):
    """Registrar autorización de prestación."""
    try:
        data = {
            'fecha_autorizacion': request.form.get('fecha_autorizacion'),
            'importe_profesional_autorizado': request.form.get('importe_profesional_autorizado'),
            'importe_afiliado_autorizado': request.form.get('importe_afiliado_autorizado'),
            'importe_coseguro_autorizado': request.form.get('importe_coseguro_autorizado'),
            'observaciones_autorizacion': request.form.get('observaciones_autorizacion'),
        }
        
        # TODO: Manejar upload de archivo
        # if 'autorizacion_adjunta' in request.files:
        #     file = request.files['autorizacion_adjunta']
        #     # Guardar archivo y actualizar path
        
        prestacion = RegistrarAutorizacionPrestacionService.execute(prestacion_id, data)
        flash('Autorización registrada exitosamente', 'success')
        
    except EstadoPrestacionInvalidoError as e:
        flash(str(e), 'error')
    except OdontoAppError as e:
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar autorización: {str(e)}', 'error')
    
    return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))


@main_bp.route('/prestaciones/<int:prestacion_id>/cobro', methods=['POST'])
@login_required
def registrar_cobro_prestacion(prestacion_id: int):
    """Registrar un cobro en prestación."""
    try:
        data = {
            'fecha_cobro': request.form.get('fecha_cobro'),
            'tipo_cobro': request.form.get('tipo_cobro'),
            'monto': request.form.get('monto'),
            'razon': request.form.get('razon'),
            'usuario_id': current_user.id if current_user.is_authenticated else None,
        }
        
        cobro = RegistrarCobroPrestacionService.execute(prestacion_id, data)
        flash('Cobro registrado exitosamente', 'success')
        
    except OdontoAppError as e:
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar cobro: {str(e)}', 'error')
    
    return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))


@main_bp.route('/prestaciones/<int:prestacion_id>/realizar', methods=['POST'])
@login_required
def realizar_prestacion(prestacion_id: int):
    """Marcar prestación como realizada."""
    try:
        data = {
            'fecha_realizacion': request.form.get('fecha_realizacion'),
        }
        
        prestacion = RegistrarRealizacionPrestacionService.execute(prestacion_id, data)
        flash('Prestación marcada como realizada', 'success')
        
    except (PrestacionNoAutorizadaError, FechasRealizacionInvalidasError, OdontoAppError) as e:
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al marcar como realizada: {str(e)}', 'error')
    
    return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))


@main_bp.route('/prestaciones/<int:prestacion_id>/item/<int:item_id>/realizar', methods=['POST'])
@login_required
def marcar_item_realizado(prestacion_id: int, item_id: int):
    """Marcar un ítem individual de práctica como realizado."""
    try:
        data = {
            'fecha_realizacion_item': request.form.get('fecha_realizacion_item') or None,
        }
        
        MarcarItemRealizadoService.execute(item_id, data)
        flash('Práctica marcada como realizada', 'success')
        
    except OdontoAppError as e:
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al marcar práctica como realizada: {str(e)}', 'error')
    
    return redirect(url_for('main.ver_prestacion', prestacion_id=prestacion_id))
