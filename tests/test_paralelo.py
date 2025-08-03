#!/usr/bin/env python3
"""
Script de prueba para verificar el procesamiento paralelo
"""

import os
import sys
import time
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parallel_processor import (
    procesar_correos_paralelo, 
    configurar_concurrencia, 
    obtener_estadisticas_paralelo
)
from gmail_utils import gmail_service_oauth, listar_correos
from execution_control import obtener_ultima_ejecucion
from config import get_config
from cloud_logging import get_logger

def probar_procesamiento_paralelo():
    """Prueba el procesamiento paralelo con correos reales."""
    
    print("🚀 PRUEBA: PROCESAMIENTO PARALELO")
    print("=" * 60)
    
    try:
        # Obtener configuración
        config = get_config()
        print(f"✅ Configuración: {config.gcp_project}")
        
        # Mostrar configuración actual de paralelización
        stats = obtener_estadisticas_paralelo()
        print(f"📊 Configuración de paralelización:")
        print(f"   - Hilos simultáneos: {stats['configuracion']['max_workers']}")
        print(f"   - Timeout por correo: {stats['configuracion']['timeout_por_correo']}s")
        print(f"   - Mejora esperada: {stats['mejora_esperada']}")
        
        # Obtener correos de prueba (solo 10 para la prueba)
        service = gmail_service_oauth()
        print("✅ Servicio de Gmail inicializado")
        
        # Obtener correos de las últimas 24 horas
        from datetime import timedelta
        fecha_desde = datetime.utcnow() - timedelta(hours=24)
        
        correos = listar_correos(service, max_results=10, fecha_desde=fecha_desde)
        print(f"📧 Correos encontrados para prueba: {len(correos)}")
        
        if not correos:
            print("⚠️ No se encontraron correos para procesar")
            return False
        
        # Probar procesamiento paralelo
        print(f"\n🔄 Iniciando procesamiento paralelo...")
        tiempo_inicio = time.time()
        
        resultados = procesar_correos_paralelo(correos, max_workers=3)  # Usar 3 hilos para prueba
        
        tiempo_fin = time.time()
        duracion = tiempo_fin - tiempo_inicio
        
        # Analizar resultados
        completados = len([r for r in resultados if r['estado'] == 'completado'])
        ignorados = len([r for r in resultados if r['estado'] == 'ignorado'])
        ya_procesados = len([r for r in resultados if r['estado'] == 'ya_procesado'])
        errores = len([r for r in resultados if r['estado'] == 'error'])
        
        print(f"\n📊 Resultados del procesamiento paralelo:")
        print(f"   - Duración total: {duracion:.2f} segundos")
        print(f"   - Completados: {completados}")
        print(f"   - Ignorados: {ignorados}")
        print(f"   - Ya procesados: {ya_procesados}")
        print(f"   - Errores: {errores}")
        
        # Calcular mejora estimada
        tiempo_secuencial_estimado = len(correos) * 1.1  # 1.1s por correo estimado
        mejora = ((tiempo_secuencial_estimado - duracion) / tiempo_secuencial_estimado) * 100
        
        print(f"\n⚡ Rendimiento:")
        print(f"   - Tiempo secuencial estimado: {tiempo_secuencial_estimado:.2f}s")
        print(f"   - Tiempo paralelo real: {duracion:.2f}s")
        print(f"   - Mejora real: {mejora:.1f}%")
        
        # Mostrar detalles de cada correo
        print(f"\n📋 Detalles por correo:")
        print("-" * 80)
        
        for i, resultado in enumerate(resultados, 1):
            print(f"{i}. ID: {resultado['id']}")
            print(f"   Estado: {resultado['estado']}")
            if resultado['estado'] == 'error':
                print(f"   Error: {resultado.get('error', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def probar_configuracion_concurrencia():
    """Prueba la configuración de concurrencia."""
    
    print("\n🔧 PRUEBA: CONFIGURACIÓN DE CONCURRENCIA")
    print("=" * 50)
    
    try:
        # Configuración original
        stats_original = obtener_estadisticas_paralelo()
        print(f"📊 Configuración original: {stats_original['configuracion']}")
        
        # Cambiar configuración
        configurar_concurrencia(max_workers=8, timeout=45)
        
        # Verificar cambios
        stats_nueva = obtener_estadisticas_paralelo()
        print(f"📊 Configuración nueva: {stats_nueva['configuracion']}")
        
        # Restaurar configuración original
        configurar_concurrencia(
            max_workers=stats_original['configuracion']['max_workers'],
            timeout=stats_original['configuracion']['timeout_por_correo']
        )
        
        print("✅ Configuración de concurrencia probada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def simular_rendimiento():
    """Simula el rendimiento esperado con diferentes configuraciones."""
    
    print("\n📈 SIMULACIÓN DE RENDIMIENTO")
    print("=" * 50)
    
    configuraciones = [
        {'hilos': 1, 'desc': 'Secuencial (actual)'},
        {'hilos': 3, 'desc': 'Paralelo conservador'},
        {'hilos': 5, 'desc': 'Paralelo balanceado'},
        {'hilos': 8, 'desc': 'Paralelo agresivo'},
        {'hilos': 10, 'desc': 'Paralelo máximo'}
    ]
    
    correos_ejemplo = 200
    tiempo_por_correo = 1.1  # segundos
    
    print(f"📊 Simulación para {correos_ejemplo} correos ({tiempo_por_correo}s por correo):")
    print("-" * 80)
    
    for config in configuraciones:
        hilos = config['hilos']
        desc = config['desc']
        
        if hilos == 1:
            tiempo_estimado = correos_ejemplo * tiempo_por_correo
        else:
            tiempo_estimado = (correos_ejemplo * tiempo_por_correo) / hilos
        
        mejora = ((correos_ejemplo * tiempo_por_correo - tiempo_estimado) / (correos_ejemplo * tiempo_por_correo)) * 100
        
        print(f"🔄 {desc}:")
        print(f"   - Hilos: {hilos}")
        print(f"   - Tiempo estimado: {tiempo_estimado:.1f}s")
        print(f"   - Mejora: {mejora:.1f}%")
        print()

def main():
    """Función principal de pruebas."""
    
    print("🧪 PRUEBAS DE PROCESAMIENTO PARALELO")
    print("=" * 80)
    
    # Prueba 1: Configuración de concurrencia
    if probar_configuracion_concurrencia():
        print("✅ Configuración de concurrencia: OK")
    else:
        print("❌ Configuración de concurrencia: FALLÓ")
        return
    
    # Prueba 2: Simulación de rendimiento
    simular_rendimiento()
    
    # Prueba 3: Procesamiento real (opcional)
    print("🤔 ¿Quieres ejecutar una prueba real con correos? (s/n): ", end="")
    respuesta = input().lower().strip()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        if probar_procesamiento_paralelo():
            print("✅ Procesamiento paralelo: OK")
        else:
            print("❌ Procesamiento paralelo: FALLÓ")
    else:
        print("⏭️ Prueba real omitida")
    
    print("\n🎉 Pruebas completadas")
    print("📝 Próximos pasos:")
    print("   1. Ejecutar: python src/app.py")
    print("   2. Verificar logs en Cloud Console")
    print("   3. Comparar tiempos de ejecución")

if __name__ == "__main__":
    main() 