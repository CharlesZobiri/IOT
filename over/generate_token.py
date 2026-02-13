#!/usr/bin/env python3
"""
Générateur de tokens sécurisés pour l'API REST
Génère des tokens cryptographiquement sécurisés
"""
import secrets
import sys
import argparse

def generate_token(length=32):
    """
    Génère un token sécurisé aléatoire
    
    Args:
        length: Longueur du token en bytes (par défaut 32 = 64 caractères hex)
    
    Returns:
        Token hexadécimal sécurisé
    """
    # Génère des bytes aléatoires cryptographiquement sécurisés
    token_bytes = secrets.token_bytes(length)
    # Convertit en hexadécimal (chaque byte = 2 caractères hex)
    token = token_bytes.hex()
    return token

def generate_url_safe_token(length=32):
    """
    Génère un token sécurisé compatible URL (base64url)
    
    Args:
        length: Longueur du token en bytes
    
    Returns:
        Token base64url sécurisé
    """
    import base64
    token_bytes = secrets.token_bytes(length)
    # Encode en base64url (sans padding, compatible URL)
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
    return token

def main():
    parser = argparse.ArgumentParser(
        description='Générateur de tokens sécurisés pour l\'API REST',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Générer un token par défaut (64 caractères hex)
  python3 generate_token.py
  
  # Générer un token plus long (128 caractères hex)
  python3 generate_token.py --length 64
  
  # Générer un token URL-safe (base64url)
  python3 generate_token.py --url-safe
  
  # Générer plusieurs tokens
  python3 generate_token.py --count 5
        """
    )
    
    parser.add_argument(
        '--length',
        type=int,
        default=32,
        help='Longueur du token en bytes (défaut: 32 = 64 caractères hex)'
    )
    
    parser.add_argument(
        '--url-safe',
        action='store_true',
        help='Génère un token compatible URL (base64url)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Nombre de tokens à générer (défaut: 1)'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Affiche la commande export pour copier-coller'
    )
    
    args = parser.parse_args()
    
    # Validation
    if args.length < 16:
        print("⚠️  Attention: Les tokens de moins de 16 bytes (32 caractères) ne sont pas recommandés pour la sécurité", file=sys.stderr)
    
    if args.length > 128:
        print("⚠️  Attention: Les tokens très longs peuvent causer des problèmes de performance", file=sys.stderr)
    
    print("=" * 60)
    print("GÉNÉRATION DE TOKENS SÉCURISÉS")
    print("=" * 60)
    print()
    
    tokens = []
    
    for i in range(args.count):
        if args.url_safe:
            token = generate_url_safe_token(args.length)
        else:
            token = generate_token(args.length)
        
        tokens.append(token)
        
        print(f"Token {i+1}:")
        print(f"  {token}")
        print()
    
    if args.export:
        print("=" * 60)
        print("COMMANDES EXPORT (copier-coller):")
        print("=" * 60)
        print()
        
        if len(tokens) == 1:
            print(f"export API_TOKEN='{tokens[0]}'")
        else:
            print(f"export API_TOKENS='{','.join(tokens)}'")
        print()
    
    print("=" * 60)
    print("UTILISATION:")
    print("=" * 60)
    print()
    print("1. Pour un seul token:")
    print(f"   export API_TOKEN='{tokens[0]}'")
    print()
    print("2. Pour plusieurs tokens:")
    print(f"   export API_TOKENS='{','.join(tokens)}'")
    print()
    print("3. Dans systemd (service):")
    print("   Ajouter dans /etc/systemd/system/api-rest.service:")
    print("   [Service]")
    print(f"   Environment=\"API_TOKEN={tokens[0]}\"")
    print()
    print("4. Tester le token:")
    print(f"   curl -H 'Authorization: Bearer {tokens[0]}' http://localhost:5000/api/dashboard")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
