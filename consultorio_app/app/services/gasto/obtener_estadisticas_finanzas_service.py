"""
Servicio para obtener estadísticas financieras.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import func, and_, or_

from app.database import db
from app.models import (
    Gasto,
    ObraSocial,
    Paciente,
    Practica,
    Prestacion,
    PrestacionPractica,
    PrestacionCobro,
)


class ObtenerEstadisticasFinanzasService:
    """Servicio para obtener estadísticas financieras."""
    
    @staticmethod
    def obtener_resumen(
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        paciente_id: Optional[int] = None
    ) -> Dict:
        """
        Obtiene resumen financiero con ingresos, egresos y balance.
        
        Los ingresos ahora se calculan desde PrestacionCobro (lo efectivamente cobrado),
        separando:
        - Cobros a pacientes (de PrestacionCobro)
        - Importes profesionales autorizados por obras sociales (pendientes de cobro a OS)
        
        Args:
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
            paciente_id: ID del paciente para filtrar ingresos (opcional)
            
        Returns:
            Diccionario con resumen financiero
        """
        # Calcular ingresos de cobros a pacientes (PrestacionCobro)
        query_cobros_pacientes = db.session.query(
            func.sum(PrestacionCobro.monto).label('total')
        ).join(Prestacion, PrestacionCobro.prestacion_id == Prestacion.id)
        
        filtros_cobros = []
        if fecha_desde:
            filtros_cobros.append(PrestacionCobro.fecha_cobro >= fecha_desde)
        if fecha_hasta:
            filtros_cobros.append(PrestacionCobro.fecha_cobro <= fecha_hasta)
        if paciente_id:
            filtros_cobros.append(Prestacion.paciente_id == paciente_id)
        
        if filtros_cobros:
            query_cobros_pacientes = query_cobros_pacientes.filter(and_(*filtros_cobros))
        
        total_cobros_pacientes = query_cobros_pacientes.scalar() or Decimal('0')
        
        # Calcular ingresos por cobrar a obras sociales (importe_profesional_autorizado)
        # de prestaciones autorizadas en el período
        query_os = db.session.query(
            func.sum(Prestacion.importe_profesional_autorizado).label('total')
        ).filter(Prestacion.fecha_autorizacion.isnot(None))
        
        filtros_os = []
        if fecha_desde:
            filtros_os.append(Prestacion.fecha_autorizacion >= fecha_desde)
        if fecha_hasta:
            filtros_os.append(Prestacion.fecha_autorizacion <= fecha_hasta)
        if paciente_id:
            filtros_os.append(Prestacion.paciente_id == paciente_id)
        
        if filtros_os:
            query_os = query_os.filter(and_(*filtros_os))
        
        total_pendiente_os = query_os.scalar() or Decimal('0')
        
        # Calcular egresos (de Gastos)
        query_egresos = db.session.query(
            func.sum(Gasto.monto).label('total')
        )
        
        filtros_egresos = []
        if fecha_desde:
            filtros_egresos.append(Gasto.fecha >= fecha_desde)
        if fecha_hasta:
            filtros_egresos.append(Gasto.fecha <= fecha_hasta)
        
        if filtros_egresos:
            query_egresos = query_egresos.filter(and_(*filtros_egresos))
        
        total_egresos = query_egresos.scalar() or Decimal('0')
        
        # Calcular balance
        # Total ingresos = solo cobros de pacientes (prácticas PLUS efectivamente cobradas)
        # Los pendientes de OS NO son ingresos directos de la doctora
        total_cobros_pacientes = Decimal(total_cobros_pacientes)
        total_pendiente_os = Decimal(total_pendiente_os)
        total_egresos = Decimal(total_egresos)
        
        total_ingresos = total_cobros_pacientes  # Solo cobros efectivos
        balance = total_ingresos - total_egresos
        
        return {
            'ingresos': float(total_ingresos),
            'ingresos_pacientes': float(total_cobros_pacientes),
            'ingresos_os_pendiente': float(total_pendiente_os),  # Se mantiene para referencia
            'egresos': float(total_egresos),
            'balance': float(balance),
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }
    
    @staticmethod
    def obtener_ingresos_por_tipo(
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Dict]:
        """
        Obtiene ingresos agrupados por tipo de cobro (método de pago).
        
        Usa PrestacionCobro.tipo_cobro para agrupar por: 
        transferencia, efectivo, débito, crédito, otros.
        
        Args:
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
            
        Returns:
            Lista de diccionarios con tipo_cobro y total
        """
        query = db.session.query(
            PrestacionCobro.tipo_cobro.label('tipo'),
            func.sum(PrestacionCobro.monto).label('total'),
            func.count(PrestacionCobro.id).label('cantidad')
        ).group_by(PrestacionCobro.tipo_cobro)
        
        filtros = []
        if fecha_desde:
            filtros.append(PrestacionCobro.fecha_cobro >= fecha_desde)
        if fecha_hasta:
            filtros.append(PrestacionCobro.fecha_cobro <= fecha_hasta)
        
        if filtros:
            query = query.filter(and_(*filtros))
        
        resultados = query.all()
        
        # Mapear nombres amigables
        tipo_nombres = {
            'transferencia': 'Transferencia',
            'efectivo': 'Efectivo',
            'debito': 'Débito',
            'credito': 'Crédito',
            'otros': 'Otros'
        }
        
        return [
            {
                'fuente': tipo_nombres.get(tipo, tipo.capitalize() if tipo else 'Sin especificar'),
                'total': float(total),
                'cantidad': cantidad
            }
            for tipo, total, cantidad in resultados
        ]

    @staticmethod
    def obtener_ingresos_por_practica(
        obra_social: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Dict]:
        """
        Obtiene ingresos agrupados por práctica (código + descripción).

        Calcula el monto real basándose en PrestacionCobro (lo efectivamente cobrado),
        considerando solo prácticas PLUS que son los ingresos reales de la doctora.

        Args:
            obra_social: Nombre de la obra social ("Particular" considera pacientes sin obra social)
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)

        Returns:
            Lista de diccionarios con código, descripción, cantidad y total
        """
        session = db.session
        
        # Agrupar por práctica desde PrestacionCobro (lo efectivamente cobrado)
        # Necesitamos asociar cada cobro con las prácticas PLUS de esa prestación
        query = session.query(
            Practica.codigo.label('codigo'),
            Practica.descripcion.label('descripcion'),
            func.count(PrestacionCobro.id).label('cantidad_cobros'),
            func.sum(PrestacionCobro.monto).label('monto_total')
        ).join(Prestacion, PrestacionCobro.prestacion_id == Prestacion.id)
        query = query.join(PrestacionPractica, PrestacionPractica.prestacion_id == Prestacion.id)
        query = query.join(Practica, PrestacionPractica.practica_id == Practica.id)
        query = query.join(Paciente, Prestacion.paciente_id == Paciente.id)
        query = query.outerjoin(ObraSocial, Paciente.obra_social_id == ObraSocial.id)
        
        # Solo contar prácticas no anuladas
        query = query.filter(PrestacionPractica.fecha_anulacion.is_(None))
        
        filtros = []
        
        # Filtrar por fecha de cobro (lo que realmente importa)
        if fecha_desde:
            filtros.append(PrestacionCobro.fecha_cobro >= fecha_desde)
        if fecha_hasta:
            filtros.append(PrestacionCobro.fecha_cobro <= fecha_hasta)

        # Filtrar por obra social si se especifica
        if obra_social and obra_social.lower() not in ('todas', 'todo'):
            if obra_social.lower() == 'particular':
                # Solo prácticas PLUS para particulares
                filtros.append(Practica.es_plus == True)
                filtros.append(or_(ObraSocial.nombre == 'Particular', ObraSocial.id.is_(None)))
            else:
                # Para obras sociales específicas, solo prácticas NO-PLUS
                filtros.append(Practica.es_plus == False)
                filtros.append(func.lower(ObraSocial.nombre) == obra_social.lower())
        else:
            # Cuando es "Todo", solo mostrar prácticas PLUS (ingresos reales de la doctora)
            # Las prácticas de obra social NO son ingresos directos
            filtros.append(Practica.es_plus == True)
        
        if filtros:
            query = query.filter(and_(*filtros))
        
        query = query.group_by(Practica.codigo, Practica.descripcion)

        resultados = query.all()
        
        practicas_data = []
        for row in resultados:
            codigo = row.codigo or 'Sin código'
            descripcion = row.descripcion or 'Sin descripción'
            
            practicas_data.append({
                'codigo': codigo,
                'descripcion': descripcion,
                'cantidad': int(row.cantidad_cobros or 0),
                'total': float(row.monto_total or 0)
            })

        # Ordenar por total desc
        return sorted(
            practicas_data,
            key=lambda x: x['total'],
            reverse=True
        )
    
    @staticmethod
    def obtener_egresos_por_categoria(
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Dict]:
        """
        Obtiene egresos agrupados por categoría.
        
        Args:
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
            
        Returns:
            Lista de diccionarios con categoría y total
        """
        query = db.session.query(
            Gasto.categoria,
            func.sum(Gasto.monto).label('total'),
            func.count(Gasto.id).label('cantidad')
        ).group_by(Gasto.categoria)
        
        filtros = []
        if fecha_desde:
            filtros.append(Gasto.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(Gasto.fecha <= fecha_hasta)
        
        if filtros:
            query = query.filter(and_(*filtros))
        
        resultados = query.all()
        
        return [
            {
                'categoria': categoria,
                'total': float(total),
                'cantidad': cantidad
            }
            for categoria, total, cantidad in resultados
        ]
    
    @staticmethod
    def obtener_detalle_prestaciones(
        obra_social: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limite: int = 50
    ) -> List[Dict]:
        """
        Obtiene detalle de prestaciones individuales para una obra social.
        
        Ahora muestra montos reales:
        - Total cobrado al paciente (suma de PrestacionCobro)
        - Importe profesional autorizado (a cobrar de OS)
        
        Args:
            obra_social: Nombre de la obra social (opcional)
            fecha_desde: Fecha desde (opcional)
            fecha_hasta: Fecha hasta (opcional)
            limite: Número máximo de registros a devolver
            
        Returns:
            Lista de diccionarios con detalles de cada prestación
        """
        query = db.session.query(
            Prestacion.id,
            Prestacion.fecha_solicitud,
            Prestacion.fecha_autorizacion,
            Prestacion.estado,
            Prestacion.importe_afiliado_autorizado,
            Prestacion.importe_profesional_autorizado,
            Paciente.nombre.label('paciente_nombre'),
            Paciente.apellido.label('paciente_apellido'),
            func.coalesce(ObraSocial.nombre, 'Particular').label('obra_social_nombre')
        ).join(Paciente, Prestacion.paciente_id == Paciente.id)
        query = query.outerjoin(ObraSocial, Paciente.obra_social_id == ObraSocial.id)
        
        filtros = []
        if fecha_desde:
            filtros.append(
                or_(
                    Prestacion.fecha_autorizacion >= fecha_desde,
                    Prestacion.fecha_solicitud >= fecha_desde
                )
            )
        if fecha_hasta:
            filtros.append(
                or_(
                    Prestacion.fecha_autorizacion <= fecha_hasta,
                    Prestacion.fecha_solicitud <= fecha_hasta
                )
            )
        
        if obra_social and obra_social.lower() not in ('todas', 'todo'):
            if obra_social.lower() == 'particular':
                filtros.append(or_(ObraSocial.nombre == 'Particular', ObraSocial.id.is_(None)))
            else:
                filtros.append(func.lower(ObraSocial.nombre) == obra_social.lower())
        
        if filtros:
            query = query.filter(and_(*filtros))
        
        query = query.order_by(Prestacion.fecha_solicitud.desc()).limit(limite)
        resultados = query.all()
        
        # Obtener prácticas y cobros asociados a cada prestación
        prestaciones_detalle = []
        for row in resultados:
            # Obtener prácticas de esta prestación (solo PLUS para pacientes)
            practicas_query = db.session.query(
                Practica.codigo,
                Practica.descripcion,
                Practica.es_plus,
                PrestacionPractica.cantidad
            ).join(PrestacionPractica, Practica.id == PrestacionPractica.practica_id)
            practicas_query = practicas_query.filter(
                PrestacionPractica.prestacion_id == row.id,
                PrestacionPractica.fecha_anulacion.is_(None)
            )
            practicas = practicas_query.all()
            
            # Formatear prácticas como string
            practicas_str = ', '.join([
                f"{p.codigo} ({p.cantidad})" + (' [PLUS]' if p.es_plus else '')
                for p in practicas
            ])
            
            # Obtener total cobrado al paciente
            total_cobrado = db.session.query(
                func.sum(PrestacionCobro.monto)
            ).filter(
                PrestacionCobro.prestacion_id == row.id
            ).scalar() or 0
            
            prestaciones_detalle.append({
                'id': row.id,
                'fecha': row.fecha_autorizacion or row.fecha_solicitud,
                'estado': row.estado,
                'paciente': f"{row.paciente_nombre} {row.paciente_apellido}",
                'practicas': practicas_str,
                'monto_paciente': float(row.importe_afiliado_autorizado or 0),
                'cobrado_paciente': float(total_cobrado),
                'monto_os': float(row.importe_profesional_autorizado or 0),
                'obra_social': row.obra_social_nombre
            })
        
        return prestaciones_detalle
    
    @staticmethod
    def obtener_evolucion_mensual(anio: int) -> Dict:
        """
        Obtiene evolución de ingresos y egresos por mes.
        
        Args:
            anio: Año para el reporte
            
        Returns:
            Diccionario con datos mensuales
        """
        # Nombres de meses en español
        nombres_meses = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        meses_data = []
        
        for mes in range(1, 13):
            # Primer y último día del mes
            if mes == 12:
                fecha_desde = date(anio, mes, 1)
                fecha_hasta = date(anio + 1, 1, 1) - timedelta(days=1)
            else:
                fecha_desde = date(anio, mes, 1)
                fecha_hasta = date(anio, mes + 1, 1) - timedelta(days=1)
            
            # Obtener resumen del mes
            resumen = ObtenerEstadisticasFinanzasService.obtener_resumen(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            meses_data.append({
                'mes': mes,
                'nombre': nombres_meses[mes - 1],
                'ingresos': resumen['ingresos'],
                'egresos': resumen['egresos'],
                'balance': resumen['balance']
            })
        
        return {
            'anio': anio,
            'meses': meses_data
        }
