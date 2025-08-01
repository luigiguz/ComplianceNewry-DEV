#!/usr/bin/env python3
"""
Script de migración para implementar ventana dinámica
Agrega las columnas necesarias a la tabla de control de ejecuciones
"""

import os
import sys
import psycopg2
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from postgres_utils import get_postgres_connection
from config import get_config

def ejecutar_migracion():
    """Ejecuta la migración para agregar columnas de ventana dinámica."""
    
    print("🚀 Iniciando migración para ventana dinámica...")
    
    try:
        # Obtener configuración
        config = get_config()
        print(f"✅ Configuración cargada - Proyecto: {config.gcp_project}")
        
        # Conectar a PostgreSQL
        conn = get_postgres_connection()
        cursor = conn.cursor()
        print("✅ Conexión a PostgreSQL establecida")
        
        # Verificar si las columnas ya existen
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'compliance_db' 
            AND table_name = 'ComplianceEjecuciones'
            AND column_name IN ('FechaInicioVentana', 'FechaFinVentana', 'TipoVentana')
        """)
        
        columnas_existentes = [row[0] for row in cursor.fetchall()]
        
        if len(columnas_existentes) == 3:
            print("✅ Las columnas de ventana dinámica ya existen")
            return True
        
        print(f"📋 Columnas existentes: {columnas_existentes}")
        print("🔧 Agregando columnas faltantes...")
        
        # Agregar columnas una por una
        columnas_a_agregar = [
            ("FechaInicioVentana", "TIMESTAMP"),
            ("FechaFinVentana", "TIMESTAMP"),
            ("TipoVentana", "VARCHAR(50) DEFAULT 'dinamica'")
        ]
        
        for nombre_columna, tipo_columna in columnas_a_agregar:
            if nombre_columna not in columnas_existentes:
                try:
                    query = f"""
                    ALTER TABLE compliance_db."ComplianceEjecuciones" 
                    ADD COLUMN "{nombre_columna}" {tipo_columna}
                    """
                    cursor.execute(query)
                    print(f"✅ Columna '{nombre_columna}' agregada")
                except Exception as e:
                    print(f"⚠️  Error agregando columna '{nombre_columna}': {e}")
        
        # Crear índice para mejorar consultas
        try:
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_compliance_ejecuciones_ventana 
            ON compliance_db."ComplianceEjecuciones" ("FechaInicioVentana", "FechaFinVentana")
            """)
            print("✅ Índice de ventana creado")
        except Exception as e:
            print(f"⚠️  Error creando índice: {e}")
        
        # Commit de los cambios
        conn.commit()
        print("✅ Cambios confirmados en la base de datos")
        
        # Verificar la estructura final
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'compliance_db' 
            AND table_name = 'ComplianceEjecuciones'
            ORDER BY ordinal_position
        """)
        
        columnas_finales = cursor.fetchall()
        print("\n📊 Estructura final de la tabla:")
        print("-" * 60)
        for columna in columnas_finales:
            print(f"  {columna[0]:<25} {columna[1]:<15} {columna[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migración completada exitosamente!")
        print("✅ El sistema ahora soporta ventana dinámica")
        print("📝 Próximos pasos:")
        print("   1. Reiniciar la aplicación")
        print("   2. Probar el nuevo comportamiento")
        print("   3. Verificar logs para confirmar funcionamiento")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

def verificar_migracion():
    """Verifica que la migración se aplicó correctamente."""
    
    print("\n🔍 Verificando migración...")
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Verificar columnas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'compliance_db' 
            AND table_name = 'ComplianceEjecuciones'
            AND column_name IN ('FechaInicioVentana', 'FechaFinVentana', 'TipoVentana')
        """)
        
        columnas = [row[0] for row in cursor.fetchall()]
        
        if len(columnas) == 3:
            print("✅ Migración verificada correctamente")
            print(f"   Columnas encontradas: {', '.join(columnas)}")
            return True
        else:
            print("❌ Migración incompleta")
            print(f"   Columnas esperadas: 3, encontradas: {len(columnas)}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRACIÓN: VENTANA DINÁMICA")
    print("=" * 60)
    
    # Ejecutar migración
    if ejecutar_migracion():
        # Verificar migración
        verificar_migracion()
    else:
        print("❌ La migración falló")
        sys.exit(1) 