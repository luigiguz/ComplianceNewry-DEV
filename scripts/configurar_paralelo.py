#!/usr/bin/env python3
"""
Script para configurar rápidamente la paralelización
"""

import os
import sys

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parallel_processor import configurar_concurrencia, obtener_estadisticas_paralelo

def mostrar_configuracion_actual():
    """Muestra la configuración actual de paralelización."""
    stats = obtener_estadisticas_paralelo()
    
    print("📊 Configuración actual de paralelización:")
    print(f"   - Hilos simultáneos: {stats['configuracion']['max_workers']}")
    print(f"   - Timeout por correo: {stats['configuracion']['timeout_por_correo']}s")
    print(f"   - Mejora esperada: {stats['mejora_esperada']}")
    print()

def configurar_rapidamente():
    """Configura la paralelización de forma interactiva."""
    
    print("🚀 CONFIGURADOR DE PARALELIZACIÓN")
    print("=" * 50)
    
    mostrar_configuracion_actual()
    
    print("Opciones de configuración:")
    print("1. Conservador (3 hilos) - Menor riesgo, mejora 67%")
    print("2. Balanceado (5 hilos) - Equilibrio, mejora 80%")
    print("3. Agresivo (8 hilos) - Máxima velocidad, mejora 87%")
    print("4. Personalizado")
    print("5. Mantener configuración actual")
    
    try:
        opcion = input("\nSelecciona una opción (1-5): ").strip()
        
        if opcion == "1":
            configurar_concurrencia(max_workers=3, timeout=30)
            print("✅ Configurado modo conservador (3 hilos)")
            
        elif opcion == "2":
            configurar_concurrencia(max_workers=5, timeout=30)
            print("✅ Configurado modo balanceado (5 hilos)")
            
        elif opcion == "3":
            configurar_concurrencia(max_workers=8, timeout=45)
            print("✅ Configurado modo agresivo (8 hilos)")
            
        elif opcion == "4":
            print("\nConfiguración personalizada:")
            try:
                hilos = int(input("Número de hilos (1-10): "))
                timeout = int(input("Timeout por correo en segundos (15-120): "))
                
                if 1 <= hilos <= 10 and 15 <= timeout <= 120:
                    configurar_concurrencia(max_workers=hilos, timeout=timeout)
                    print(f"✅ Configurado: {hilos} hilos, {timeout}s timeout")
                else:
                    print("❌ Valores fuera de rango")
                    return
                    
            except ValueError:
                print("❌ Valores inválidos")
                return
                
        elif opcion == "5":
            print("✅ Manteniendo configuración actual")
            
        else:
            print("❌ Opción inválida")
            return
            
        print("\n📊 Nueva configuración:")
        mostrar_configuracion_actual()
        
        print("🎯 Próximos pasos:")
        print("   1. Ejecutar: python src/app.py")
        print("   2. Probar: python tests/test_paralelo.py")
        print("   3. Verificar logs en Cloud Console")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Configuración cancelada")

def main():
    """Función principal."""
    configurar_rapidamente()

if __name__ == "__main__":
    main() 