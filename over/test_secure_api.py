#!/usr/bin/env python3
"""
Test de la version sécurisée de l'API
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour importer l'API sécurisée
sys.path.insert(0, str(Path(__file__).parent))

# Importer et tester
from test_auth_token_with_server import *

if __name__ == "__main__":
    # Modifier le chemin de l'API pour utiliser la version sécurisée
    import test_auth_token_with_server as test_module
    
    # Remplacer le chemin de l'API dans le module
    original_api_path = Path(test_module.__file__).parent.parent / "api_rest" / "api.py"
    secure_api_path = Path(__file__).parent / "api_secure.py"
    
    # Modifier la fonction start_api pour utiliser la version sécurisée
    def start_api_secure():
        """Démarre l'API sécurisée en arrière-plan"""
        global API_PROCESS
        print(f"{BLUE}Démarrage de l'API sécurisée...{RESET}")
        
        env = os.environ.copy()
        env["API_TOKEN"] = TEST_TOKEN
        
        try:
            API_PROCESS = subprocess.Popen(
                [sys.executable, str(secure_api_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(secure_api_path.parent.parent)
            )
            
            # Attendre que l'API démarre
            for i in range(10):
                time.sleep(1)
                try:
                    response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
                    if response.status_code == 200:
                        print(f"{GREEN}API sécurisée démarrée avec succès{RESET}\n")
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
    
    # Remplacer la fonction start_api
    test_module.start_api = start_api_secure
    
    # Exécuter les tests
    sys.exit(test_module.main())
