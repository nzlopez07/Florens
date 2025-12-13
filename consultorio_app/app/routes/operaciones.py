from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from app.database.session import DatabaseSession
from app.models import Operacion, Paciente, Codigo
from . import main_bp


@main_bp.route('/operaciones')
def listar_operaciones():
    """Lista todas las operaciones.
    
    ---
    tags:
      - Operaciones
    responses:
      200:
        description: Lista de operaciones obtenida exitosamente
    """
    operaciones = Operacion.query.order_by(Operacion.fecha.desc()).all()
    return render_template('operaciones/lista.html', operaciones=operaciones)


@main_bp.route('/operaciones/nueva', methods=['GET', 'POST'])
def nueva_operacion():
    """Crear una nueva operación.
    
    ---
    tags:
      - Operaciones
    parameters:
      - name: paciente_id
        in: form
        type: integer
        required: true
        description: ID del paciente
      - name: descripcion
        in: form
        type: string
        required: true
        description: Descripción de la operación
      - name: monto
        in: form
        type: number
        required: true
        description: Monto de la operación
      - name: codigo_id
        in: form
        type: integer
        description: ID del código de operación
      - name: observaciones
        in: form
        type: string
        description: Observaciones adicionales
    responses:
      200:
        description: Formulario para crear operación (GET) o operación creada (POST)
      302:
        description: Redirección después de crear operación exitosamente
    """
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
