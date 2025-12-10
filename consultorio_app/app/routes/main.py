"""Legacy routes file deprecated in favor of split modules."""

@main_bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
def crear_paciente():
    """Crear un nuevo paciente"""
    if request.method == 'POST':
        try:
            paciente = Paciente(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                dni=request.form['dni'],
                fecha_nac=datetime.strptime(request.form['fecha_nac'], '%Y-%m-%d').date() if request.form.get('fecha_nac') else None,
                telefono=request.form.get('telefono'),
                direccion=request.form.get('direccion'),
                obra_social_id=int(request.form['obra_social_id']) if request.form.get('obra_social_id') else None,
                """
                Legacy routes file superseded by modular route modules:
                - routes/index.py
                - routes/pacientes.py
                - routes/turnos.py
                - routes/operaciones.py

                Left intentionally minimal to avoid duplicate blueprints.
                """
            db.session.commit()
