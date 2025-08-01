#!/usr/bin/env python3
"""
Script para verificar la estructura exacta de la tabla ComplianceEjecuciones
"""

import os
import sys

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from postgres_utils import get_postgres_connection
from config import get_config

def check_table_structure():
    """Verifica la estructura exacta de la tabla ComplianceEjecuciones."""
    
    print("🔍 Verificando estructura de la tabla ComplianceEjecuciones...")
    print("=" * 60)
    
    try:
        # Obtener configuración
        config = get_config()
        print(f"✅ Configuración: {config.gcp_project}")
        
        # Conectar a PostgreSQL
        conn = get_postgres_connection()
        cursor = conn.cursor()
        print("✅ Conexión a PostgreSQL establecida")
        
        # Verificar todas las columnas de la tabla
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns 
            WHERE table_schema = 'compliance_db' 
            AND table_name = 'ComplianceEjecuciones'
            ORDER BY ordinal_position
        """)
        
        columnas = cursor.fetchall()
        print(f"📋 Total de columnas encontradas: {len(columnas)}")
        print("\n📊 Estructura de la tabla:")
        print("-" * 80)
        print(f"{'Pos':<3} {'Nombre':<25} {'Tipo':<20} {'Nullable':<8} {'Default':<15}")
        print("-" * 80)
        
        for columna in columnas:
            nombre = columna[0]
            tipo = columna[1]
            nullable = columna[2]
            default = columna[3] or 'NULL'
            pos = columna[4]
            
            print(f"{pos:<3} {nombre:<25} {tipo:<20} {nullable:<8} {default:<15}")
        
        # Verificar específicamente las columnas de ventana
        print("\n🔍 Verificando columnas de ventana dinámica:")
        print("-" * 50)
        
        columnas_ventana = ['fechainicioventana', 'fechafinventana', 'tipoventana']
        for col_ventana in columnas_ventana:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'compliance_db' 
                AND table_name = 'ComplianceEjecuciones'
                AND column_name = %s
            """, (col_ventana,))
            
            resultado = cursor.fetchone()
            if resultado:
                print(f"✅ {resultado[0]}: {resultado[1]}")
            else:
                print(f"❌ {col_ventana}: NO ENCONTRADA")
        
        # Verificar columnas principales
        print("\n🔍 Verificando columnas principales:")
        print("-" * 50)
        
        columnas_principales = ['id', 'fechaejecucion', 'ultimafechacorreo', 'correosprocesados', 'estado', 'duracionsegundos', 'modo', 'fechacreacion']
        for col_principal in columnas_principales:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'compliance_db' 
                AND table_name = 'ComplianceEjecuciones'
                AND column_name = %s
            """, (col_principal,))
            
            resultado = cursor.fetchone()
            if resultado:
                print(f"✅ {resultado[0]}: {resultado[1]}")
            else:
                print(f"❌ {col_principal}: NO ENCONTRADA")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Verificación completada")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

if __name__ == "__main__":
    check_table_structure() 