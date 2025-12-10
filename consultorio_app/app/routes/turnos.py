from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash
from app.database.session import DatabaseSession
from app.models import Turno, Paciente, Estado
from . import main_bp


@main_bp.route('/turnos')
def listar_turnos():
    """Lista todos los turnos, opcionalmente filtrados por fecha."""
    fecha_filtro = request.args.get('fecha')
    query = Turno.query

    if fecha_filtro:
        fecha_obj = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
        query = query.filter_by(fecha=fecha_obj)
    else:
        query = query.filter(Turno.fecha >= date.today())

    turnos = query.order_by(Turno.fecha, Turno.hora).all()
    return render_template('turnos/lista.html', turnos=turnos, fecha_filtro=fecha_filtro)


@main_bp.route('/turnos/nuevo', methods=['GET', 'POST'])
def nuevo_turno():
    """Crear un nuevo turno."""
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
