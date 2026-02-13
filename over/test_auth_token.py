#!/usr/bin/env python3
"""
Script de test pour l'authentification par token de l'API REST
Teste les différentes méthodes d'authentification et les cas d'erreur
"""

import requests
import sys
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
TEST_TOKEN = os.getenv("TEST_TOKEN", "test-token-123")
INVALID_TOKEN = "invalid-token-xyz"

# Couleurs pour l'affichage
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_test(name):
    print(f"\n{YELLOW}=== Test: {name} ==={RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"  {message}")

def test_health_endpoint():
    """Test de l'endpoint /api/health (sans authentification)"""
    print_test("Endpoint /api/health (sans token)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_without_token():
    """Test d'un endpoint protégé sans token"""
    print_test("Endpoint protégé SANS token")
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard")
        if response.status_code == 401:
            print_success(f"Status: {response.status_code} (attendu)")
            print_info(f"Réponse: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code} (attendu: 401)")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_with_invalid_token():
    """Test avec un token invalide"""
    print_test("Endpoint protégé avec token INVALIDE")
    
    # Test avec Authorization Bearer
    try:
        headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers)
        if response.status_code == 401:
            print_success(f"Authorization Bearer - Status: {response.status_code} (attendu)")
            print_info(f"Réponse: {response.json()}")
        else:
            print_error(f"Authorization Bearer - Status: {response.status_code} (attendu: 401)")
            return False
    except Exception as e:
        print_error(f"Erreur Authorization Bearer: {e}")
        return False
    
    # Test avec X-API-KEY
    try:
        headers = {"X-API-KEY": INVALID_TOKEN}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers)
        if response.status_code == 401:
            print_success(f"X-API-KEY - Status: {response.status_code} (attendu)")
        else:
            print_error(f"X-API-KEY - Status: {response.status_code} (attendu: 401)")
            return False
    except Exception as e:
        print_error(f"Erreur X-API-KEY: {e}")
        return False
    
    # Test avec query parameter
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard?token={INVALID_TOKEN}")
        if response.status_code == 401:
            print_success(f"Query parameter - Status: {response.status_code} (attendu)")
        else:
            print_error(f"Query parameter - Status: {response.status_code} (attendu: 401)")
            return False
    except Exception as e:
        print_error(f"Erreur query parameter: {e}")
        return False
    
    return True

def test_with_valid_token_bearer():
    """Test avec token valide via Authorization Bearer"""
    print_test("Token valide via Authorization Bearer")
    try:
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers)
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.json()}")
            return True
        elif response.status_code == 401:
            print_error(f"Status: {response.status_code} - Token rejeté")
            print_info("Vérifiez que le token est configuré dans les variables d'environnement")
            return False
        else:
            print_error(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.text}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_with_valid_token_x_api_key():
    """Test avec token valide via X-API-KEY"""
    print_test("Token valide via X-API-KEY")
    try:
        headers = {"X-API-KEY": TEST_TOKEN}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers)
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.json()}")
            return True
        elif response.status_code == 401:
            print_error(f"Status: {response.status_code} - Token rejeté")
            return False
        else:
            print_error(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_with_valid_token_query():
    """Test avec token valide via query parameter"""
    print_test("Token valide via query parameter (?token=...)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard?token={TEST_TOKEN}")
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.json()}")
            return True
        elif response.status_code == 401:
            print_error(f"Status: {response.status_code} - Token rejeté")
            return False
        else:
            print_error(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_other_endpoints():
    """Test des autres endpoints protégés"""
    print_test("Autres endpoints protégés")
    
    endpoints = [
        ("GET", "/api/history/temperature"),
        ("GET", "/api/photos"),
    ]
    
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    results = []
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json={})
            
            if response.status_code in [200, 404]:  # 404 acceptable si pas de données
                print_success(f"{method} {endpoint} - Status: {response.status_code}")
                results.append(True)
            elif response.status_code == 401:
                print_error(f"{method} {endpoint} - Status: 401 (non autorisé)")
                results.append(False)
            else:
                print_info(f"{method} {endpoint} - Status: {response.status_code}")
                results.append(True)  # Autres erreurs peuvent être acceptables
        except Exception as e:
            print_error(f"{method} {endpoint} - Erreur: {e}")
            results.append(False)
    
    return all(results)

def main():
    print(f"\n{YELLOW}{'='*60}")
    print("TEST D'AUTHENTIFICATION PAR TOKEN - API REST")
    print(f"{'='*60}{RESET}\n")
    print(f"URL de l'API: {API_BASE_URL}")
    print(f"Token de test: {TEST_TOKEN}")
    print(f"\n{RED}Note: Assurez-vous que l'API est démarrée et que le token est configuré{RESET}\n")
    
    results = []
    
    # Tests sans authentification
    results.append(("Health endpoint", test_health_endpoint()))
    results.append(("Sans token", test_without_token()))
    results.append(("Token invalide", test_with_invalid_token()))
    
    # Tests avec token valide
    results.append(("Token Bearer", test_with_valid_token_bearer()))
    results.append(("Token X-API-KEY", test_with_valid_token_x_api_key()))
    results.append(("Token query param", test_with_valid_token_query()))
    
    # Tests autres endpoints
    results.append(("Autres endpoints", test_other_endpoints()))
    
    # Résumé
    print(f"\n{YELLOW}{'='*60}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*60}{RESET}\n")
    
    passed = 0
    failed = 0
    
    for name, result in results:
        if result:
            print_success(f"{name}")
            passed += 1
        else:
            print_error(f"{name}")
            failed += 1
    
    print(f"\n{GREEN}Tests réussis: {passed}{RESET}")
    if failed > 0:
        print(f"{RED}Tests échoués: {failed}{RESET}")
    
    print(f"\n{YELLOW}Pour configurer le token, utilisez:")
    print(f"  export API_TOKEN='votre-token'")
    print(f"  ou")
    print(f"  export API_TOKENS='token1,token2,token3'{RESET}\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
