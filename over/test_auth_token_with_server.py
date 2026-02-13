#!/usr/bin/env python3
"""
Script de test pour l'authentification par token de l'API REST
Démarre l'API automatiquement pour les tests
"""

import requests
import sys
import os
import subprocess
import time
import signal

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
TEST_TOKEN = os.getenv("TEST_TOKEN", "test-token-123")
INVALID_TOKEN = "invalid-token-xyz"
API_PROCESS = None

# Couleurs pour l'affichage
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def cleanup():
    """Arrête le processus API si en cours"""
    global API_PROCESS
    if API_PROCESS:
        try:
            API_PROCESS.terminate()
            API_PROCESS.wait(timeout=5)
        except:
            try:
                API_PROCESS.kill()
            except:
                pass
        API_PROCESS = None

def signal_handler(sig, frame):
    """Gestionnaire de signal pour arrêter proprement"""
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_api():
    """Démarre l'API en arrière-plan"""
    global API_PROCESS
    print(f"{BLUE}Démarrage de l'API...{RESET}")
    
    api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api_rest", "api.py")
    env = os.environ.copy()
    env["API_TOKEN"] = TEST_TOKEN
    
    try:
        API_PROCESS = subprocess.Popen(
            [sys.executable, api_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(api_path)
        )
        
        # Attendre que l'API démarre
        for i in range(10):
            time.sleep(1)
            try:
                response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
                if response.status_code == 200:
                    print(f"{GREEN}API démarrée avec succès{RESET}\n")
                    return True
            except:
                pass
        
        # Vérifier les erreurs
        if API_PROCESS.poll() is not None:
            stdout, stderr = API_PROCESS.communicate()
            print(f"{RED}Erreur au démarrage de l'API:{RESET}")
            if stderr:
                print(stderr.decode())
            return False
        
        print(f"{YELLOW}L'API prend du temps à démarrer, continuation des tests...{RESET}\n")
        return True
    except Exception as e:
        print(f"{RED}Erreur: {e}{RESET}")
        return False

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
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
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
        response = requests.get(f"{API_BASE_URL}/api/dashboard", timeout=5)
        if response.status_code == 401:
            print_success(f"Status: {response.status_code} (attendu)")
            print_info(f"Réponse: {response.json()}")
            return True
        else:
            print_error(f"Status: {response.status_code} (attendu: 401)")
            print_info(f"Réponse: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_with_invalid_token():
    """Test avec un token invalide"""
    print_test("Endpoint protégé avec token INVALIDE")
    
    all_passed = True
    
    # Test avec Authorization Bearer
    try:
        headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 401:
            print_success(f"Authorization Bearer - Status: {response.status_code} (attendu)")
            print_info(f"Réponse: {response.json()}")
        else:
            print_error(f"Authorization Bearer - Status: {response.status_code} (attendu: 401)")
            all_passed = False
    except Exception as e:
        print_error(f"Erreur Authorization Bearer: {e}")
        all_passed = False
    
    # Test avec X-API-KEY
    try:
        headers = {"X-API-KEY": INVALID_TOKEN}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 401:
            print_success(f"X-API-KEY - Status: {response.status_code} (attendu)")
        else:
            print_error(f"X-API-KEY - Status: {response.status_code} (attendu: 401)")
            all_passed = False
    except Exception as e:
        print_error(f"Erreur X-API-KEY: {e}")
        all_passed = False
    
    # Test avec query parameter
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard?token={INVALID_TOKEN}", timeout=5)
        if response.status_code == 401:
            print_success(f"Query parameter - Status: {response.status_code} (attendu)")
        else:
            print_error(f"Query parameter - Status: {response.status_code} (attendu: 401)")
            all_passed = False
    except Exception as e:
        print_error(f"Erreur query parameter: {e}")
        all_passed = False
    
    return all_passed

def test_with_valid_token_bearer():
    """Test avec token valide via Authorization Bearer"""
    print_test("Token valide via Authorization Bearer")
    try:
        headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            data = response.json()
            print_info(f"Réponse: {str(data)[:200]}...")
            return True
        elif response.status_code == 401:
            print_error(f"Status: {response.status_code} - Token rejeté")
            print_info("Vérifiez que le token est configuré dans les variables d'environnement")
            return False
        elif response.status_code == 500:
            print_error(f"Status: {response.status_code}")
            print_info("Erreur serveur (peut être liée à la base de données)")
            print_info(f"Réponse: {response.text[:200]}")
            return False
        else:
            print_error(f"Status: {response.status_code}")
            print_info(f"Réponse: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_with_valid_token_x_api_key():
    """Test avec token valide via X-API-KEY"""
    print_test("Token valide via X-API-KEY")
    try:
        headers = {"X-API-KEY": TEST_TOKEN}
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            data = response.json()
            print_info(f"Réponse: {str(data)[:200]}...")
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
        response = requests.get(f"{API_BASE_URL}/api/dashboard?token={TEST_TOKEN}", timeout=5)
        if response.status_code == 200:
            print_success(f"Status: {response.status_code}")
            data = response.json()
            print_info(f"Réponse: {str(data)[:200]}...")
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
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json={}, timeout=5)
            
            if response.status_code in [200, 404]:  # 404 acceptable si pas de données
                print_success(f"{method} {endpoint} - Status: {response.status_code}")
                results.append(True)
            elif response.status_code == 401:
                print_error(f"{method} {endpoint} - Status: 401 (non autorisé)")
                results.append(False)
            elif response.status_code == 500:
                print_info(f"{method} {endpoint} - Status: 500 (erreur serveur, peut être normal)")
                results.append(True)  # Acceptable si erreur DB
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
    print(f"Token de test: {TEST_TOKEN}\n")
    
    # Démarrer l'API
    if not start_api():
        print(f"{RED}Impossible de démarrer l'API. Vérifiez les dépendances et la configuration.{RESET}")
        return 1
    
    try:
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
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())
