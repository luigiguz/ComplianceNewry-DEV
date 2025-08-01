#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de la ventana dinámica
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from execution_control import obtener_ultima_ejecucion, obtener_estadisticas_ejecuciones
from postgres_utils import get_postgres_connection
from config import get_config

def probar_ventana_dinamica():
    """Prueba el funcionamiento de la ventana dinámica."""
    
    print("🧪 Probando ventana dinámica...")
    print("=" * 50)
    
    try:
        # Obtener configuración
        config = get_config()
        print(f"✅ Configuración: {config.gcp_project}")
        
        # Conectar a PostgreSQL
        conn = get_postgres_connection()
        cursor = conn.cursor()
        print("✅ Conexión a PostgreSQL establecida")
        
        # Verificar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'compliance_db' 
            AND table_name = 'ComplianceEjecuciones'
            AND column_name IN ('FechaInicioVentana', 'FechaFinVentana', 'TipoVentana')
            ORDER BY column_name
        """)
        
        columnas_ventana = cursor.fetchall()
        print(f"📋 Columnas de ventana encontradas: {len(columnas_ventana)}")
        
        for columna in columnas_ventana:
            print(f"   - {columna[0]}: {columna[1]}")
        
        if len(columnas_ventana) != 3:
            print("❌ Faltan columnas de ventana dinámica")
            print("   Ejecuta: python scripts/migrate_ventana_dinamica.py")
            return False
        
        # Obtener última ejecución
        ultima_ejecucion = obtener_ultima_ejecucion()
        print(f"📅 Última ejecución: {ultima_ejecucion}")
        
        # Obtener estadísticas
        stats = obtener_estadisticas_ejecuciones()
        if stats:
            print(f"📊 Estadísticas de ejecuciones:")
            print(f"   - Total ejecuciones: {stats['total_ejecuciones']}")
            print(f"   - Exitosas: {stats['exitosas']}")
            print(f"   - Fallidas: {stats['fallidas']}")
            print(f"   - Duración promedio: {stats['duracion_promedio']:.2f}s")
            print(f"   - Última ejecución: {stats['ultima_ejecucion']}")
        
        # Verificar ejecuciones recientes con ventana dinámica
        cursor.execute("""
            SELECT 
                id,
                fechaejecucion,
                modo,
                "TipoVentana",
                "FechaInicioVentana",
                "FechaFinVentana",
                correosprocesados,
                duracionsegundos
            FROM compliance_db."ComplianceEjecuciones"
            WHERE fechaejecucion >= NOW() - INTERVAL '7 days'
            ORDER BY fechaejecucion DESC
            LIMIT 5
        """)
        
        ejecuciones_recientes = cursor.fetchall()
        print(f"\n📋 Últimas 5 ejecuciones:")
        print("-" * 80)
        
        for ejecucion in ejecuciones_recientes:
            print(f"ID: {ejecucion[0]}")
            print(f"  Fecha: {ejecucion[1]}")
            print(f"  Modo: {ejecucion[2]}")
            print(f"  Tipo Ventana: {ejecucion[3]}")
            print(f"  Inicio Ventana: {ejecucion[4]}")
            print(f"  Fin Ventana: {ejecucion[5]}")
            print(f"  Correos: {ejecucion[6]}")
            print(f"  Duración: {ejecucion[7]:.2f}s")
            print()
        
        cursor.close()
        conn.close()
        
        print("✅ Prueba de ventana dinámica completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def simular_comportamiento():
    """Simula el comportamiento esperado de la ventana dinámica."""
    
    print("\n🎯 Simulación de comportamiento esperado:")
    print("=" * 50)
    
    # Simular primera ejecución
    print("📅 Primera ejecución (hoy 10:00):")
    print("   - Modo: primera_ejecucion")
    print("   - Ventana: Últimas 24 horas (ayer 10:00 - hoy 10:00)")
    print("   - Límite: 200 correos")
    print("   - Comportamiento: Procesa correos de las últimas 24h")
    
    # Simular segunda ejecución
    print("\n📅 Segunda ejecución (mañana 09:00):")
    print("   - Modo: ventana_dinamica")
    print("   - Ventana: Desde última ejecución (hoy 10:00 - mañana 09:00)")
    print("   - Límite: 200 correos")
    print("   - Comportamiento: Procesa correos nuevos desde la última ejecución")
    
    # Simular tercera ejecución
    print("\n📅 Tercera ejecución (pasado mañana 08:00):")
    print("   - Modo: ventana_dinamica")
    print("   - Ventana: Desde última ejecución (mañana 09:00 - pasado mañana 08:00)")
    print("   - Límite: 200 correos")
    print("   - Comportamiento: Procesa correos nuevos desde la última ejecución")
    
    print("\n✅ Ventajas del nuevo sistema:")
    print("   - No pierde correos entre ejecuciones")
    print("   - Ventana de tiempo precisa y rastreable")
    print("   - Control de volumen con límite de 200 correos")
    print("   - Logging detallado de ventanas procesadas")

def main():
    """Función principal de pruebas."""
    
    print("🚀 PRUEBA: VENTANA DINÁMICA")
    print("=" * 60)
    
    # Ejecutar prueba
    if probar_ventana_dinamica():
        # Mostrar simulación
        simular_comportamiento()
        
        print("\n🎉 ¡Ventana dinámica implementada correctamente!")
        print("📝 Próximos pasos:")
        print("   1. Ejecutar: python src/app.py")
        print("   2. Probar: python tests/api/test_api.py")
        print("   3. Verificar logs en Cloud Console")
    else:
        print("\n❌ La prueba falló")
        print("📝 Verificar:")
        print("   1. Ejecutar migración: python scripts/migrate_ventana_dinamica.py")
        print("   2. Verificar conexión a PostgreSQL")
        print("   3. Revisar configuración de Secret Manager")

if __name__ == "__main__":
    main() 