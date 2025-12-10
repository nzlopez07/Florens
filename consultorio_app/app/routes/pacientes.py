from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask import render_template, request, redirect, url_for, flash
from app.database.session import DatabaseSession
from app.models import Paciente, Turno, Operacion, Localidad, ObraSocial
from app.services import BusquedaUtils
from . import main_bp


@main_bp.route('/pacientes')
def listar_pacientes():
    """Lista todos los pacientes con funcionalidad de búsqueda."""
    termino_busqueda = request.args.get('buscar', '').strip()
    if termino_busqueda:
        pacientes = BusquedaUtils.buscar_pacientes_simple(termino_busqueda)
    else:
        pacientes = Paciente.query.all()

    return render_template(
        'pacientes/lista.html',
        pacientes=pacientes,
        termino_busqueda=termino_busqueda,
    )


@main_bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
def crear_paciente():
    """Crear un nuevo paciente."""
    session = DatabaseSession.get_instance().session

    if request.method == 'POST':
        try:
            paciente = Paciente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                dni=request.form['dni'],
                fecha_nac=datetime.strptime(request.form['fecha_nac'], '%Y-%m-%d').date()
                if request.form.get('fecha_nac')
                else None,
                telefono=request.form.get('telefono'),
                direccion=request.form.get('direccion'),
                obra_social_id=int(request.form['obra_social_id']) if request.form.get('obra_social_id') else None,
                localidad_id=int(request.form['localidad_id']) if request.form.get('localidad_id') else None,
                carnet=request.form.get('carnet'),
                titular=request.form.get('titular'),
                parentesco=request.form.get('parentesco'),
                lugar_trabajo=request.form.get('lugar_trabajo'),
                barrio=request.form.get('barrio'),
            )

            session.add(paciente)
            session.commit()
            flash('Paciente creado exitosamente', 'success')
            return redirect(url_for('main.listar_pacientes'))
        except Exception as e:
            session.rollback()
            flash(f'Error al crear paciente: {str(e)}', 'error')

    obras_sociales = ObraSocial.query.order_by(ObraSocial.nombre).all()
    localidades = Localidad.query.order_by(Localidad.nombre).all()

    return render_template(
        'pacientes/formulario.html',
        obras_sociales=obras_sociales,
        localidades=localidades,
    )


@main_bp.route('/pacientes/<int:id>')
def ver_paciente(id: int):
    """Ver detalles de un paciente."""
    paciente = Paciente.query.get_or_404(id)

    edad = None
    if paciente.fecha_nac:
        edad = relativedelta(date.today(), paciente.fecha_nac).years

    turnos = (
        Turno.query.filter_by(paciente_id=id)
        .order_by(Turno.fecha.desc(), Turno.hora.desc())
        .all()
    )
    operaciones = (
        Operacion.query.filter_by(paciente_id=id)
        .order_by(Operacion.fecha.desc())
        .all()
    )

    estadisticas = {
        'total_turnos': len(turnos),
        'total_operaciones': len(operaciones),
    }

    return render_template(
        'pacientes/detalle.html',
        paciente=paciente,
        edad=edad,
        turnos=turnos,
        operaciones=operaciones,
        estadisticas=estadisticas,
    )


@main_bp.route('/pacientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_paciente(id: int):
    """Editar un paciente existente."""
    paciente = Paciente.query.get_or_404(id)

    session = DatabaseSession.get_instance().session

    if request.method == 'POST':
        try:
            paciente.nombre = request.form['nombre']
            paciente.apellido = request.form['apellido']
            paciente.dni = request.form['dni']
            paciente.fecha_nac = (
                datetime.strptime(request.form['fecha_nac'], '%Y-%m-%d').date()
                if request.form.get('fecha_nac')
                else None
            )
            paciente.telefono = request.form.get('telefono')
            paciente.direccion = request.form.get('direccion')
            paciente.obra_social_id = int(request.form['obra_social_id']) if request.form.get('obra_social_id') else None
            paciente.localidad_id = int(request.form['localidad_id']) if request.form.get('localidad_id') else None
            paciente.carnet = request.form.get('carnet')
            paciente.titular = request.form.get('titular')
            paciente.parentesco = request.form.get('parentesco')
            paciente.lugar_trabajo = request.form.get('lugar_trabajo')
            paciente.barrio = request.form.get('barrio')

            session.commit()
            flash('Paciente actualizado exitosamente', 'success')
            return redirect(url_for('main.ver_paciente', id=paciente.id))
        except Exception as e:
            session.rollback()
            flash(f'Error al actualizar paciente: {str(e)}', 'error')

    obras_sociales = ObraSocial.query.order_by(ObraSocial.nombre).all()
    localidades = Localidad.query.order_by(Localidad.nombre).all()

    return render_template(
        'pacientes/formulario.html',
        paciente=paciente,
        obras_sociales=obras_sociales,
        localidades=localidades,
    )
