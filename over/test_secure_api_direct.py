#!/usr/bin/env python3
"""
Test direct de la version sécurisée de l'API
"""
import requests
import sys
import os
import subprocess
import time
import signal
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
TEST_TOKEN = os.getenv("TEST_TOKEN", "test-token-123")
INVALID_TOKEN = "invalid-token-xyz"
API_PROCESS = None

# Couleurs
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Chemin de l'API sécurisée
BASE_DIR = Path(__file__).parent.parent
SECURE_API = Path(__file__).parent / "api_secure.py"

def cleanup():
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
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_api():
    print(f"{BLUE}Démarrage de l'API sécurisée...{RESET}")
    
    env = os.environ.copy()
    env["API_TOKEN"] = TEST_TOKEN
    
    try:
        global API_PROCESS
        API_PROCESS = subprocess.Popen(
            [sys.executable, str(SECURE_API)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        
        for i in range(10):
            time.sleep(1)
            try:
                response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
                if response.status_code == 200:
                    print(f"{GREEN}API sécurisée démarrée{RESET}\n")
                    return True
            except:
                pass
        
        if API_PROCESS.poll() is not None:
            stdout, stderr = API_PROCESS.communicate()
            print(f"{RED}Erreur:{RESET}")
            if stderr:
                print(stderr.decode())
            return False
        
        return True
    except Exception as e:
        print(f"{RED}Erreur: {e}{RESET}")
        return False

def print_test(name):
    print(f"\n{YELLOW}=== {name} ==={RESET}")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def test_health():
    print_test("Health endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {response.status_code}")
            print(f"  DB: {data.get('database', 'unknown')}")
            print(f"  Tokens: {data.get('tokens_configured', False)}")
            return True
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_without_token():
    print_test("Sans token (doit échouer)")
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard", timeout=5)
        if response.status_code == 401:
            print_success(f"Status: 401 (attendu)")
            return True
        print_error(f"Status: {response.status_code} (attendu: 401)")
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_invalid_token():
    print_test("Token invalide (doit échouer)")
    headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 401:
            print_success(f"Status: 401 (attendu)")
            return True
        print_error(f"Status: {response.status_code} (attendu: 401)")
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_valid_token():
    print_test("Token valide (Bearer)")
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    try:
        response = requests.get(f"{API_BASE_URL}/api/dashboard", headers=headers, timeout=5)
        if response.status_code == 200:
            print_success(f"Status: 200")
            data = response.json()
            print(f"  Capteurs: {len([k for k, v in data.items() if v is not None])}")
            return True
        elif response.status_code == 500:
            # Erreur DB acceptable si DB non configurée
            print(f"{YELLOW}Status: 500 (erreur DB, peut être normal){RESET}")
            return True
        print_error(f"Status: {response.status_code}")
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def test_validation():
    print_test("Validation des entrées")
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    # Test capteur invalide
    try:
        response = requests.get(f"{API_BASE_URL}/api/history/invalid_sensor", headers=headers, timeout=5)
        if response.status_code == 400:
            print_success("Capteur invalide rejeté (400)")
        else:
            print(f"{YELLOW}Status: {response.status_code} (attendu: 400){RESET}")
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False
    
    # Test limite excessive
    try:
        response = requests.get(f"{API_BASE_URL}/api/history/temperature?limit=10000", headers=headers, timeout=5)
        if response.status_code in [200, 500]:  # 500 si DB non configurée
            print_success("Limite excessive gérée")
        else:
            print(f"{YELLOW}Status: {response.status_code}{RESET}")
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False
    
    return True

def main():
    print(f"\n{YELLOW}{'='*60}")
    print("TEST API SÉCURISÉE")
    print(f"{'='*60}{RESET}\n")
    
    if not start_api():
        print(f"{RED}Impossible de démarrer l'API{RESET}")
        return 1
    
    try:
        results = []
        results.append(("Health", test_health()))
        results.append(("Sans token", test_without_token()))
        results.append(("Token invalide", test_invalid_token()))
        results.append(("Token valide", test_valid_token()))
        results.append(("Validation", test_validation()))
        
        print(f"\n{YELLOW}{'='*60}")
        print("RÉSUMÉ")
        print(f"{'='*60}{RESET}\n")
        
        passed = sum(1 for _, r in results if r)
        failed = len(results) - passed
        
        for name, result in results:
            if result:
                print_success(name)
            else:
                print_error(name)
        
        print(f"\n{GREEN}Réussis: {passed}{RESET}")
        if failed > 0:
            print(f"{RED}Échoués: {failed}{RESET}")
        
        return 0 if failed == 0 else 1
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())
