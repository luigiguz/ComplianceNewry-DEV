#!/usr/bin/env python3
"""
Script para probar la API de Compliance Newry
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health_check():
    """Prueba el endpoint de health check."""
    print("🔍 Probando health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_process_emails():
    """Prueba el endpoint de procesamiento de correos."""
    print("\n🔍 Probando endpoint de procesamiento de correos...")
    
    try:
        # Procesamiento automático
        print("Procesamiento automático:")
        response = requests.post(f"{API_BASE}/process-emails", json={})
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Procesamiento completado exitosamente")
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_swagger_docs():
    """Prueba el acceso a la documentación Swagger."""
    print("\n🔍 Probando acceso a documentación Swagger...")
    
    try:
        response = requests.get(f"{BASE_URL}/swagger")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Documentación Swagger accesible")
            print(f"URL: {BASE_URL}/swagger")
            return True
        else:
            print("❌ Documentación Swagger no accesible")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas de la API de Compliance Newry")
    print("=" * 50)
    
    # Verificar que la API esté corriendo
    if not test_health_check():
        print("\n❌ La API no está corriendo. Inicia la API con:")
        print("python src/app.py")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Health Check", test_health_check),
        ("Procesamiento de Correos", test_process_emails),
        ("Documentación Swagger", test_swagger_docs)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
    else:
        print("⚠️  Algunas pruebas fallaron")
    
    print(f"\n📖 Documentación disponible en: {BASE_URL}/swagger")

if __name__ == "__main__":
    main() 