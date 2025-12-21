import os
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from app.models import Prestacion
from app.services.paciente_service import PacienteService
from app.services.turno_service import TurnoService
from app.services.odontograma_service import OdontogramaService
from . import main_bp


@main_bp.route('/media/<path:filename>')
def media_file(filename: str):
  """Sirve archivos estáticos ubicados en app/media (imagen y hoja del odontograma)."""
  media_dir = os.path.join(current_app.root_path, 'media')
  return send_from_directory(media_dir, filename)


@main_bp.route('/odontograma/slots', methods=['POST'])
def guardar_slots_odontograma():
  """Guarda la configuración de slots calibrados para el odontograma."""
  data = request.get_json(silent=True) or {}
  if 'config' not in data or 'teeth' not in data:
    return jsonify({"error": "Payload inválido"}), 400
  slots_path = os.path.join(current_app.root_path, 'media', 'odontograma_slots.json')
  try:
    with open(slots_path, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})
  except Exception:
    return jsonify({"error": "No se pudo guardar la calibración"}), 500


@main_bp.route('/pacientes')
def listar_pacientes():
    """Lista todos los pacientes con funcionalidad de búsqueda.
    
    ---
    tags:
      - Pacientes
    parameters:
      - name: buscar
        in: query
        type: string
        description: Término de búsqueda por nombre, apellido o DNI
    responses:
      200:
        description: Lista de pacientes obtenida exitosamente
    """
    termino_busqueda = request.args.get('buscar', '').strip()
    pacientes = PacienteService.listar_pacientes(termino_busqueda)
    return render_template(
      'pacientes/lista.html',
      pacientes=pacientes,
      termino_busqueda=termino_busqueda,
    )


@main_bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
def crear_paciente():
    """Crear un nuevo paciente.
    
    ---
    tags:
      - Pacientes
    parameters:
      - name: nombre
        in: form
        type: string
        required: true
      - name: apellido
        in: form
        type: string
        required: true
      - name: dni
        in: form
        type: string
        required: true
      - name: fecha_nac
        in: form
        type: string
        format: date
      - name: telefono
        in: form
        type: string
      - name: direccion
        in: form
        type: string
      - name: obra_social_id
        in: form
        type: integer
      - name: localidad_id
        in: form
        type: integer
      - name: carnet
        in: form
        type: string
      - name: titular
        in: form
        type: string
      - name: parentesco
        in: form
        type: string
      - name: lugar_trabajo
        in: form
        type: string
      - name: barrio
        in: form
        type: string
    responses:
      200:
        description: Formulario para crear paciente (GET) o paciente creado (POST)
      302:
        description: Redirección después de crear paciente exitosamente
    """
    obras_sociales = PacienteService.listar_obras_sociales()
    localidades = PacienteService.listar_localidades()

    if request.method == 'POST':
        try:
            fecha_nac = datetime.strptime(request.form['fecha_nac'], '%Y-%m-%d').date() if request.form.get('fecha_nac') else None
            PacienteService.crear_paciente({
                'nombre': request.form['nombre'],
                'apellido': request.form['apellido'],
                'dni': request.form['dni'],
                'fecha_nac': fecha_nac,
                'telefono': request.form.get('telefono'),
                'direccion': request.form.get('direccion'),
                'obra_social_id': int(request.form['obra_social_id']) if request.form.get('obra_social_id') else None,
                'localidad_id': int(request.form['localidad_id']) if request.form.get('localidad_id') else None,
                'nro_afiliado': request.form.get('carnet'),
                'titular': request.form.get('titular'),
                'parentesco': request.form.get('parentesco'),
                'lugar_trabajo': request.form.get('lugar_trabajo'),
                'barrio': request.form.get('barrio'),
            })
            flash('Paciente creado exitosamente', 'success')
            return redirect(url_for('main.listar_pacientes'))
        except Exception as e:
            flash(f'Error al crear paciente: {str(e)}', 'error')

    return render_template(
        'pacientes/formulario.html',
        obras_sociales=obras_sociales,
        localidades=localidades,
    )


@main_bp.route('/pacientes/<int:id>')
def ver_paciente(id: int):
    """Ver detalles de un paciente.
    
    ---
    tags:
      - Pacientes
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID del paciente
    responses:
      200:
        description: Detalles del paciente obtenidos exitosamente
      404:
        description: Paciente no encontrado
    """
    paciente, turnos, prestaciones, edad, totales = PacienteService.obtener_detalle(id)
    if not paciente:
        return redirect(url_for('main.listar_pacientes'))

    estadisticas = {
      'total_turnos': totales['turnos'] if totales else 0,
      'total_prestaciones': totales['prestaciones'] if totales else 0,
    }

    # Obtener estado del odontograma (si está desactualizado)
    odontograma, _, desactualizado_odonto, ultima_prestacion = OdontogramaService.obtener_o_crear_actual(id)
    
    # Marcar prestaciones posteriores al odontograma
    prestaciones_nuevas = set()
    if desactualizado_odonto and odontograma.creado_en:
        for p in prestaciones:
            if p and p.fecha:
                # Convertir ambos a datetime para comparación
                prestacion_dt = p.fecha if hasattr(p.fecha, 'hour') else datetime.combine(p.fecha, datetime.min.time())
                if prestacion_dt > odontograma.creado_en:
                    prestaciones_nuevas.add(p.id)

    return render_template(
        'pacientes/detalle.html',
        paciente=paciente,
        edad=edad,
        turnos=turnos,
        prestaciones=prestaciones,
        estadisticas=estadisticas,
        desactualizado_odonto=desactualizado_odonto,
        prestaciones_nuevas=prestaciones_nuevas,
    )



@main_bp.route('/pacientes/<int:id>/odontograma')
def ver_odontograma_paciente(id: int):
    """Vista del odontograma versionado de un paciente.
    Si no existe odontograma, crea uno vacío como versión actual.
    Permite navegar versiones vía query param odontograma_id.
    """
    try:
        odontograma_id = request.args.get('odontograma_id', type=int)

        if odontograma_id:
            odontograma, versiones, desactualizado, ultima_prestacion = OdontogramaService.obtener_version(
                paciente_id=id, odontograma_id=odontograma_id
            )
            if not odontograma:
                flash('Odontograma no encontrado para este paciente', 'error')
                return redirect(url_for('main.ver_paciente', id=id))
        else:
            odontograma, versiones, desactualizado, ultima_prestacion = OdontogramaService.obtener_o_crear_actual(id)

        return render_template(
            'pacientes/odontograma.html',
            odontograma=odontograma,
            versiones=versiones,
            desactualizado=desactualizado,
            ultima_prestacion=ultima_prestacion,
        )
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.ver_paciente', id=id))


@main_bp.route('/pacientes/<int:id>/odontograma/datos')
def obtener_datos_odontograma(id: int):
    """Devuelve en JSON la versión del odontograma solicitada o la actual."""
    try:
        odontograma_id = request.args.get('odontograma_id', type=int)
        if odontograma_id:
            odontograma, versiones, desactualizado, ultima_prestacion = OdontogramaService.obtener_version(
                paciente_id=id, odontograma_id=odontograma_id
            )
            if not odontograma:
                return jsonify({"error": "Odontograma no encontrado"}), 404
        else:
            odontograma, versiones, desactualizado, ultima_prestacion = OdontogramaService.obtener_o_crear_actual(id)

        return jsonify({
            "odontograma": OdontogramaService._serializar_odontograma(odontograma),
            "versiones": [
                {
                    "id": v.id,
                    "version_seq": v.version_seq,
                    "es_actual": v.es_actual,
                    "nota_general": v.nota_general,
                    "actualizado_en": v.actualizado_en.isoformat() if v.actualizado_en else None,
                }
                for v in versiones
            ],
            "desactualizado": desactualizado,
            "ultima_prestacion": ultima_prestacion.isoformat() if ultima_prestacion else None,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@main_bp.route('/pacientes/<int:id>/odontograma/version', methods=['POST'])
def crear_version_odontograma(id: int):
    """Crea una nueva versión de odontograma aplicando cambios de caras."""
    data = request.get_json(silent=True) or {}
    cambios = data.get('caras') or []
    nota_general = data.get('nota_general')
    base_id = data.get('odontograma_base_id')

    try:
        nuevo, versiones = OdontogramaService.crear_version_desde(
            paciente_id=id,
            cambios_caras=cambios,
            nota_general=nota_general,
            base_odontograma_id=base_id,
        )

        ultima_prestacion = OdontogramaService._ultima_prestacion_timestamp(id)
        desactualizado = False
        if ultima_prestacion and (
            not nuevo.ultima_prestacion_registrada_en
            or ultima_prestacion > nuevo.ultima_prestacion_registrada_en
        ):
            desactualizado = True

        return jsonify({
            "odontograma": OdontogramaService._serializar_odontograma(nuevo),
            "versiones": [
                {
                    "id": v.id,
                    "version_seq": v.version_seq,
                    "es_actual": v.es_actual,
                    "nota_general": v.nota_general,
                    "actualizado_en": v.actualizado_en.isoformat() if v.actualizado_en else None,
                }
                for v in versiones
            ],
            "desactualizado": desactualizado,
            "ultima_prestacion": ultima_prestacion.isoformat() if ultima_prestacion else None,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "No se pudo crear la nueva versión"}), 500


@main_bp.route('/pacientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_paciente(id: int):
    """Editar un paciente existente."""
    paciente = PacienteService.obtener_paciente(id)
    if not paciente:
        return redirect(url_for('main.listar_pacientes'))

    if request.method == 'POST':
        try:
            fecha_nac = datetime.strptime(request.form['fecha_nac'], '%Y-%m-%d').date() if request.form.get('fecha_nac') else None
            PacienteService.actualizar_paciente(paciente, {
                'nombre': request.form['nombre'],
                'apellido': request.form['apellido'],
                'dni': request.form['dni'],
                'fecha_nac': fecha_nac,
                'telefono': request.form.get('telefono'),
                'direccion': request.form.get('direccion'),
                'obra_social_id': int(request.form['obra_social_id']) if request.form.get('obra_social_id') else None,
                'localidad_id': int(request.form['localidad_id']) if request.form.get('localidad_id') else None,
                'nro_afiliado': request.form.get('carnet'),
                'titular': request.form.get('titular'),
                'parentesco': request.form.get('parentesco'),
                'lugar_trabajo': request.form.get('lugar_trabajo'),
                'barrio': request.form.get('barrio'),
            })
            flash('Paciente actualizado exitosamente', 'success')
            return redirect(url_for('main.ver_paciente', id=paciente.id))
        except Exception as e:
            flash(f'Error al actualizar paciente: {str(e)}', 'error')

    obras_sociales = PacienteService.listar_obras_sociales()
    localidades = PacienteService.listar_localidades()

    return render_template(
        'pacientes/formulario.html',
        paciente=paciente,
        obras_sociales=obras_sociales,
        localidades=localidades,
    )
