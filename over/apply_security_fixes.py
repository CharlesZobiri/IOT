#!/usr/bin/env python3
"""
Script pour appliquer les corrections de sécurité à l'API
Crée une sauvegarde et remplace l'API originale par la version sécurisée
"""
import shutil
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
API_ORIGINAL = BASE_DIR / "api_rest" / "api.py"
API_SECURE = Path(__file__).parent / "api_secure.py"
BACKUP_DIR = BASE_DIR / "api_rest" / "backups"

def main():
    print("=" * 60)
    print("APPLICATION DES CORRECTIONS DE SÉCURITÉ")
    print("=" * 60)
    print()
    
    # Vérifier que les fichiers existent
    if not API_SECURE.exists():
        print(f"❌ Erreur: {API_SECURE} n'existe pas")
        return 1
    
    if not API_ORIGINAL.exists():
        print(f"❌ Erreur: {API_ORIGINAL} n'existe pas")
        return 1
    
    # Créer le répertoire de backup
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Créer une sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"api_backup_{timestamp}.py"
    
    print(f"📦 Création de la sauvegarde: {backup_file}")
    shutil.copy2(API_ORIGINAL, backup_file)
    
    # Copier la version sécurisée
    print(f"🔒 Application de la version sécurisée...")
    shutil.copy2(API_SECURE, API_ORIGINAL)
    
    # Rendre exécutable
    os.chmod(API_ORIGINAL, 0o755)
    
    print()
    print("✅ Corrections appliquées avec succès!")
    print()
    print("📋 Résumé des améliorations:")
    print("  ✓ Gestion d'erreurs DB complète")
    print("  ✓ CORS configuré de manière sécurisée")
    print("  ✓ Validation des entrées (capteurs, états, limites)")
    print("  ✓ Protection contre path traversal")
    print("  ✓ Configuration via variables d'environnement")
    print("  ✓ Logging amélioré")
    print("  ✓ Validation des paramètres")
    print()
    print("⚠️  Actions recommandées:")
    print("  1. Redémarrer le service API: sudo systemctl restart api-rest")
    print("  2. Vérifier les logs: sudo journalctl -u api-rest -f")
    print("  3. Tester l'API avec: python3 over/test_auth_token_with_server.py")
    print()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
