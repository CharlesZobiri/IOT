# Guide de Génération et Utilisation des Tokens API

## 🎯 Génération Rapide

### Token simple (recommandé)
```bash
python3 over/generate_token.py --export
```

Cela génère un token sécurisé de 64 caractères et affiche la commande `export` prête à copier-coller.

### Plusieurs tokens
```bash
python3 over/generate_token.py --count 3 --export
```

### Token URL-safe (pour utilisation dans les URLs)
```bash
python3 over/generate_token.py --url-safe --export
```

### Token plus long (plus sécurisé)
```bash
python3 over/generate_token.py --length 64 --export
```

## 📝 Utilisation

### 1. Pour un développement local

```bash
# Générer un token
TOKEN=$(python3 over/generate_token.py | grep "Token 1:" -A 1 | tail -1 | tr -d ' ')

# L'exporter
export API_TOKEN="$TOKEN"

# Démarrer l'API avec le token
cd api_rest
API_TOKEN="$TOKEN" python3 api.py
```

### 2. Pour un service systemd

1. Générer un token:
```bash
python3 over/generate_token.py
```

2. Éditer le service:
```bash
sudo nano /etc/systemd/system/api-rest.service
```

3. Ajouter dans la section `[Service]`:
```ini
[Service]
Environment="API_TOKEN=votre-token-ici"
```

4. Recharger et redémarrer:
```bash
sudo systemctl daemon-reload
sudo systemctl restart api-rest
```

### 3. Pour plusieurs tokens (rotation)

```bash
# Générer plusieurs tokens
python3 over/generate_token.py --count 3 --export
```

Puis utiliser:
```bash
export API_TOKENS='token1,token2,token3'
```

Ou dans systemd:
```ini
[Service]
Environment="API_TOKENS=token1,token2,token3"
```

## 🔐 Sécurité

### Longueur recommandée
- **Minimum**: 32 bytes (64 caractères hex) - pour développement
- **Recommandé**: 32-64 bytes (64-128 caractères hex) - pour production
- **Maximum**: 128 bytes (256 caractères hex) - très sécurisé mais peut être long

### Bonnes pratiques
1. ✅ **Ne jamais commiter les tokens dans Git**
   - Ajouter `*.env` au `.gitignore`
   - Utiliser des variables d'environnement

2. ✅ **Utiliser des tokens différents par environnement**
   - Un token pour développement
   - Un token pour production
   - Un token pour tests

3. ✅ **Roter les tokens régulièrement**
   - Générer de nouveaux tokens tous les 3-6 mois
   - Utiliser `API_TOKENS` pour permettre la transition

4. ✅ **Stockage sécurisé**
   - Variables d'environnement (pas dans le code)
   - Secrets manager en production
   - Permissions restrictives sur les fichiers de config

## 🧪 Tester un Token

### Avec curl
```bash
TOKEN="votre-token-ici"
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/dashboard
```

### Avec le script de test
```bash
TEST_TOKEN="votre-token-ici" python3 over/test_auth_token_with_server.py
```

## 📋 Exemples Complets

### Scénario 1: Développement local
```bash
# 1. Générer un token
python3 over/generate_token.py --export

# 2. Copier la commande export affichée
export API_TOKEN='...'

# 3. Démarrer l'API
cd api_rest
API_TOKEN="$API_TOKEN" python3 api.py
```

### Scénario 2: Production avec systemd
```bash
# 1. Générer un token
TOKEN=$(python3 over/generate_token.py | grep "Token 1:" -A 1 | tail -1 | tr -d ' ')

# 2. Configurer systemd
sudo tee -a /etc/systemd/system/api-rest.service > /dev/null <<EOF
[Service]
Environment="API_TOKEN=$TOKEN"
EOF

# 3. Recharger et démarrer
sudo systemctl daemon-reload
sudo systemctl restart api-rest

# 4. Vérifier
sudo systemctl status api-rest
```

### Scénario 3: Fichier .env
```bash
# 1. Générer un token
python3 over/generate_token.py --export > .env.tmp
TOKEN=$(grep "export API_TOKEN" .env.tmp | cut -d"'" -f2)

# 2. Créer le fichier .env
echo "API_TOKEN=$TOKEN" > api_rest/.env

# 3. Modifier l'API pour charger depuis .env (optionnel)
# Utiliser python-dotenv: pip install python-dotenv
```

## ⚠️ Dépannage

### Le token est rejeté
- Vérifier qu'il n'y a pas d'espaces: `echo "$API_TOKEN" | wc -c`
- Vérifier le format (hex ou base64url)
- Vérifier les logs: `sudo journalctl -u api-rest -f`

### Générer un nouveau token
```bash
# Toujours générer de nouveaux tokens, jamais réutiliser d'anciens
python3 over/generate_token.py
```

### Vérifier qu'un token est configuré
```bash
# Tester l'endpoint health
curl http://localhost:5000/api/health

# Devrait afficher: {"status":"ok","database":"...","tokens_configured":true}
```

## 🔄 Rotation de Tokens

1. Générer un nouveau token
2. Ajouter l'ancien ET le nouveau dans `API_TOKENS`
3. Mettre à jour les clients pour utiliser le nouveau
4. Retirer l'ancien token après migration complète

```bash
# Étape 1: Générer nouveau token
python3 over/generate_token.py

# Étape 2: Configurer avec les deux tokens
export API_TOKENS='ancien-token,nouveau-token'

# Étape 3: Après migration, garder seulement le nouveau
export API_TOKEN='nouveau-token'
```
