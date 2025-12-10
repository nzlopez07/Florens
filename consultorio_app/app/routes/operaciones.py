from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from app.database.session import DatabaseSession
from app.models import Operacion, Paciente, Codigo
from . import main_bp


@main_bp.route('/operaciones')
def listar_operaciones():
    """Lista todas las operaciones."""
    operaciones = Operacion.query.order_by(Operacion.fecha.desc()).all()
    return render_template('operaciones/lista.html', operaciones=operaciones)


@main_bp.route('/operaciones/nueva', methods=['GET', 'POST'])
def nueva_operacion():
    """Crear una nueva operación."""
    session = DatabaseSession.get_instance().session
    if request.method == 'POST':
        try:
            operacion = Operacion(
                paciente_id=request.form['paciente_id'],
                descripcion=request.form['descripcion'],
                monto=float(request.form['monto']),
                fecha=datetime.now(),
                codigo_id=request.form.get('codigo_id') if request.form.get('codigo_id') else None,
                observaciones=request.form.get('observaciones'),
            )

            session.add(operacion)
            session.commit()
            flash('Operación registrada exitosamente', 'success')
            return redirect(url_for('main.listar_operaciones'))
        except Exception as e:
            session.rollback()
            flash(f'Error al registrar operación: {str(e)}', 'error')

    pacientes = Paciente.query.all()
    codigos = Codigo.query.all()
    return render_template('operaciones/nueva.html', pacientes=pacientes, codigos=codigos)
