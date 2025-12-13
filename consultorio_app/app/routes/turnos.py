from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash
from sqlalchemy.orm import joinedload
from app.database.session import DatabaseSession
from app.models import Turno, Paciente, Estado, CambioEstado
from . import main_bp


ESTADOS_VALIDOS = ['Pendiente', 'Confirmado', 'Atendido', 'NoAtendido', 'Cancelado']


def _actualizar_no_atendidos(session):
    """Marca como NoAtendido los turnos vencidos que no fueron atendidos.
    Un turno se considera vencido si:
    - Su fecha es anterior a hoy, O
    - Su fecha es hoy pero su hora ya pasó
    """
    ahora = datetime.now()
    hoy = date.today()
    
    vencidos = (
        session.query(Turno)
        .options(joinedload(Turno.paciente))
        .filter(Turno.estado.is_(None) | ~Turno.estado.in_(['Atendido', 'NoAtendido', 'Cancelado']))
        .all()
    )
    
    cambios = 0
    for turno in vencidos:
        # Verificar si el turno está vencido
        es_vencido = False
        
        if turno.fecha < hoy:
            # Si la fecha es anterior a hoy, está vencido
            es_vencido = True
        elif turno.fecha == hoy and turno.hora:
            # Si es hoy, verificar si la hora ya pasó
            # Crear un datetime con la fecha y hora del turno
            turno_datetime = datetime.combine(turno.fecha, turno.hora)
            if turno_datetime < ahora:
                es_vencido = True
        
        if es_vencido:
            turno.estado = 'NoAtendido'
            cambios += 1
    
    if cambios:
        session.commit()


@main_bp.route('/turnos')
def listar_turnos():
    """Lista todos los turnos, opcionalmente filtrados por fecha.
    
    ---
    tags:
      - Turnos
    parameters:
      - name: fecha
        in: query
        type: string
        format: date
        description: Filtrar por fecha específica (YYYY-MM-DD)
      - name: buscar
        in: query
        type: string
        description: Buscar por nombre, apellido o DNI del paciente
    responses:
      200:
        description: Lista de turnos obtenida exitosamente
    """
    session = DatabaseSession.get_instance().session
    _actualizar_no_atendidos(session)

    fecha_filtro = request.args.get('fecha')
    termino = request.args.get('buscar', '').strip()

    query = session.query(Turno).options(joinedload(Turno.paciente))

    if fecha_filtro:
        fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
        query = query.filter(Turno.fecha == fecha_obj)
    else:
        query = query.filter(Turno.fecha >= date.today())

    if termino:
        like_term = f"%{termino.lower()}%"
        query = query.join(Paciente).filter(
            (Paciente.nombre.ilike(like_term)) |
            (Paciente.apellido.ilike(like_term)) |
            (Paciente.dni.ilike(like_term))
        )

    turnos = query.order_by(Turno.fecha, Turno.hora).all()
    return render_template('turnos/lista.html', turnos=turnos, fecha_filtro=fecha_filtro, termino=termino)


@main_bp.route('/turnos/nuevo', methods=['GET', 'POST'])
def nuevo_turno():
    """Crear un nuevo turno.
    
    ---
    tags:
      - Turnos
    parameters:
      - name: paciente_id
        in: form
        type: integer
        required: true
        description: ID del paciente
      - name: fecha
        in: form
        type: string
        format: date
        required: true
        description: Fecha del turno (YYYY-MM-DD)
      - name: hora
        in: form
        type: string
        required: true
        description: Hora del turno (HH:MM)
      - name: detalle
        in: form
        type: string
        description: Detalles del turno
      - name: operacion_id
        in: form
        type: integer
        description: ID de la operación
    responses:
      200:
        description: Formulario para crear turno (GET) o turno creado (POST)
      302:
        description: Redirección después de crear turno exitosamente
    """
    session = DatabaseSession.get_instance().session
    if request.method == 'POST':
        try:
            turno = Turno(
                paciente_id=request.form['paciente_id'],
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                hora=datetime.strptime(request.form['hora'], '%H:%M').time(),
                detalle=request.form.get('detalle'),
                estado=request.form.get('estado', 'Pendiente'),
            )

            session.add(turno)
            session.commit()
            flash('Turno creado exitosamente', 'success')
            return redirect(url_for('main.listar_turnos'))
        except Exception as e:
            session.rollback()
            flash(f'Error al crear turno: {str(e)}', 'error')

    pacientes = Paciente.query.all()
    estados = Estado.query.all()
    return render_template('turnos/nuevo.html', pacientes=pacientes, estados=estados)


@main_bp.route('/turnos/<int:turno_id>/estado', methods=['POST'])
def cambiar_estado_turno(turno_id: int):
    """Cambiar el estado de un turno con reglas de negocio básicas.
    
    ---
    tags:
      - Turnos
    parameters:
      - name: turno_id
        in: path
        type: integer
        required: true
        description: ID del turno
      - name: estado
        in: form
        type: string
        required: true
        enum: ['Pendiente', 'Confirmado', 'Atendido', 'NoAtendido', 'Cancelado']
        description: Nuevo estado del turno
    responses:
      302:
        description: Redirección después de cambiar el estado
      404:
        description: Turno no encontrado
      400:
        description: Estado inválido
    """
    session = DatabaseSession.get_instance().session
    nuevo_estado = request.form.get('estado')

    if nuevo_estado not in ESTADOS_VALIDOS:
        flash('Estado inválido', 'error')
        return redirect(url_for('main.listar_turnos'))

    turno = session.get(Turno, turno_id)
    if not turno:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('main.listar_turnos'))

    # Regla: no se puede cancelar si ya es NoAtendido
    if nuevo_estado == 'Cancelado' and (turno.estado == 'NoAtendido'):
        flash('No se puede cancelar un turno marcado como NoAtendido.', 'warning')
        return redirect(url_for('main.listar_turnos'))

    # Guardar estado anterior para el historial
    estado_anterior = turno.estado or 'Pendiente'

    # Regla: si está vencido y no atendido, forzar NoAtendido
    if turno.fecha < date.today() and nuevo_estado not in ['Atendido', 'NoAtendido']:
        turno.estado = 'NoAtendido'
    else:
        turno.estado = nuevo_estado

    try:
        # Registrar cambio de estado
        cambio = CambioEstado(
            turno_id=turno.id,
            estado_anterior=estado_anterior,
            estado_nuevo=turno.estado,
            fecha_cambio=datetime.now(),
            motivo=f'Cambio de estado desde interfaz de usuario'
        )
        session.add(cambio)
        session.commit()
        flash('Estado actualizado', 'success')
    except Exception as exc:
        session.rollback()
        flash(f'Error al actualizar estado: {exc}', 'error')

    return redirect(url_for('main.listar_turnos'))


@main_bp.route('/turnos/<int:turno_id>/eliminar', methods=['POST'])
def eliminar_turno(turno_id: int):
    """Eliminar un turno. Solo se pueden eliminar turnos Pendientes.
    
    ---
    tags:
      - Turnos
    parameters:
      - name: turno_id
        in: path
        type: integer
        required: true
        description: ID del turno a eliminar
    responses:
      302:
        description: Redirección después de eliminar el turno
      404:
        description: Turno no encontrado
      400:
        description: No se puede eliminar un turno que no está Pendiente
    """
    session = DatabaseSession.get_instance().session
    
    turno = session.get(Turno, turno_id)
    if not turno:
        flash('Turno no encontrado', 'error')
        return redirect(url_for('main.listar_turnos'))
    
    # Regla: solo se pueden eliminar turnos Pendientes
    estado_actual = turno.estado or 'Pendiente'
    if estado_actual != 'Pendiente':
        flash(f'Solo se pueden eliminar turnos Pendientes. Este turno está: {estado_actual}', 'warning')
        return redirect(url_for('main.listar_turnos'))
    
    try:
        session.delete(turno)
        session.commit()
        flash('Turno eliminado exitosamente', 'success')
    except Exception as exc:
        session.rollback()
        flash(f'Error al eliminar turno: {exc}', 'error')
    
    return redirect(url_for('main.listar_turnos'))
