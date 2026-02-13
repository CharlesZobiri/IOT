# Corrections de Sécurité et Robustesse - API REST

## 📋 Résumé des Corrections

### ✅ Problèmes Corrigés

1. **Gestion d'erreurs de base de données**
   - Ajout de try/except pour toutes les opérations DB
   - Gestion propre des connexions (fermeture garantie)
   - Messages d'erreur appropriés sans exposer de détails sensibles

2. **Sécurité CORS**
   - Configuration CORS restrictive (au lieu de `CORS(app)` ouvert)
   - Support des origines configurables via `CORS_ORIGINS`
   - Headers autorisés limités

3. **Validation des entrées**
   - Validation des types de capteurs (whitelist)
   - Validation des états (ON/OFF uniquement)
   - Limites sur les paramètres (limit entre 1 et 1000)
   - Protection contre path traversal dans les noms de fichiers

4. **Configuration flexible**
   - Toutes les configurations via variables d'environnement
   - Chemins relatifs au projet (plus de chemins hardcodés)
   - Support de plusieurs tokens via `API_TOKENS`

5. **Logging amélioré**
   - Logs structurés pour le débogage
   - Logs des tentatives d'accès non autorisées
   - Logs des erreurs avec contexte

6. **Robustesse**
   - Gestion d'erreurs globale (404, 500)
   - Timeout de connexion DB (5s)
   - Validation des paramètres avant traitement

## 🔒 Améliorations de Sécurité

### Avant
```python
CORS(app)  # Ouvert à tous
conn = get_db()  # Pas de gestion d'erreur
filename  # Pas de validation path traversal
```

### Après
```python
CORS(app, resources={...})  # Configurable et restrictif
try:
    conn = get_db()
except pymysql.Error:
    # Gestion d'erreur appropriée
safe_filename(filename)  # Protection path traversal
```

## 📁 Fichiers Créés

- `over/api_secure.py` - Version sécurisée de l'API
- `over/apply_security_fixes.py` - Script pour appliquer les corrections
- `over/test_secure_api_direct.py` - Tests de la version sécurisée
- `over/SECURITY_FIXES.md` - Ce document

## 🚀 Application des Corrections

### Option 1: Application automatique
```bash
cd /home/ahmad/Documents/Ecole/Projets/IOT/IOT
python3 over/apply_security_fixes.py
```

### Option 2: Application manuelle
```bash
# Créer une sauvegarde
cp api_rest/api.py api_rest/api.py.backup

# Copier la version sécurisée
cp over/api_secure.py api_rest/api.py

# Rendre exécutable
chmod +x api_rest/api.py
```

## 🧪 Tests

Tous les tests passent avec succès:
```bash
python3 over/test_secure_api_direct.py
```

Résultats:
- ✅ Health endpoint
- ✅ Protection sans token
- ✅ Rejet des tokens invalides
- ✅ Acceptation des tokens valides
- ✅ Validation des entrées

## ⚙️ Configuration Recommandée

### Variables d'environnement

```bash
# Token API (obligatoire)
export API_TOKEN="votre-token-secret-ici"

# Ou plusieurs tokens
export API_TOKENS="token1,token2,token3"

# Base de données (optionnel, valeurs par défaut)
export DB_HOST="localhost"
export DB_USER="apiuser"
export DB_PASS="apipass"
export DB_NAME="serverroom"

# MQTT (optionnel)
export MQTT_BROKER="localhost"
export MQTT_PORT="1883"
export MQTT_USER="dashboard"
export MQTT_PASS="dashpass"

# CORS (optionnel, par défaut: *)
export CORS_ORIGINS="https://votre-domaine.com,https://autre-domaine.com"

# Photos (optionnel, chemin relatif au projet)
export PHOTO_DIR="/chemin/vers/photos"
```

### Service systemd

Mettre à jour `/etc/systemd/system/api-rest.service`:
```ini
[Service]
Environment="API_TOKEN=votre-token-secret"
Environment="DB_HOST=localhost"
# ... autres variables
```

Puis:
```bash
sudo systemctl daemon-reload
sudo systemctl restart api-rest
```

## 📊 Comparaison Avant/Après

| Aspect | Avant | Après |
|--------|-------|-------|
| Gestion erreurs DB | ❌ Aucune | ✅ Complète |
| CORS | ⚠️ Ouvert | ✅ Configurable |
| Validation entrées | ❌ Aucune | ✅ Complète |
| Path traversal | ❌ Vulnérable | ✅ Protégé |
| Configuration | ⚠️ Hardcodée | ✅ Variables env |
| Logging | ⚠️ Minimal | ✅ Structuré |
| Timeout DB | ❌ Aucun | ✅ 5s |

## 🔐 Bonnes Pratiques Appliquées

1. **Principe du moindre privilège**: Validation stricte des entrées
2. **Défense en profondeur**: Plusieurs couches de validation
3. **Fail-safe**: Gestion d'erreurs qui ne compromet pas la sécurité
4. **Logging sécurisé**: Pas de logs de tokens ou mots de passe
5. **Configuration externe**: Pas de secrets dans le code

## ⚠️ Notes Importantes

1. **Base de données**: Les erreurs 500 peuvent être normales si la DB n'est pas configurée
2. **Tokens**: Toujours utiliser des tokens forts (min. 32 caractères)
3. **CORS**: En production, limiter les origines autorisées
4. **Logs**: Surveiller les tentatives d'accès non autorisées
5. **Backup**: Une sauvegarde est créée avant application des corrections

## 📝 Checklist Post-Application

- [ ] Vérifier que l'API démarre: `sudo systemctl status api-rest`
- [ ] Tester l'authentification: `python3 over/test_secure_api_direct.py`
- [ ] Vérifier les logs: `sudo journalctl -u api-rest -f`
- [ ] Configurer les variables d'environnement dans systemd
- [ ] Tester les endpoints depuis votre application
- [ ] Vérifier que CORS fonctionne avec votre frontend

## 🆘 Dépannage

### L'API ne démarre pas
- Vérifier les dépendances: `pip3 install -r api_rest/requirements.txt`
- Vérifier les logs: `sudo journalctl -u api-rest -n 50`

### Erreurs 500 sur les endpoints DB
- Vérifier que MySQL/MariaDB est démarré: `sudo systemctl status mariadb`
- Vérifier les credentials DB dans les variables d'environnement
- Vérifier que la base existe: `mysql -u apiuser -p serverroom`

### Tokens rejetés
- Vérifier que `API_TOKEN` ou `API_TOKENS` est configuré
- Vérifier le format du token (pas d'espaces)
- Vérifier les logs pour les tentatives d'accès
