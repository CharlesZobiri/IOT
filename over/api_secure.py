#!/usr/bin/env python3
"""
Version sécurisée et robuste de l'API REST
Corrections apportées:
- Gestion d'erreurs DB complète
- Sécurité CORS configurée
- Validation des entrées
- Protection contre path traversal
- Validation des paramètres
- Configuration flexible
"""
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import functools
import hmac
import os
import pymysql
import paho.mqtt.publish as publish
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration CORS sécurisée
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-KEY"]
    }
})

# Configuration DB (avec variables d'environnement)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "apiuser")
DB_PASS = os.getenv("DB_PASS", "apipass")
DB_NAME = os.getenv("DB_NAME", "serverroom")

# Configuration MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "dashboard")
MQTT_PASS = os.getenv("MQTT_PASS", "dashpass")

# Configuration API Tokens
API_TOKENS = [t.strip() for t in os.getenv("API_TOKENS", "").split(",") if t.strip()]
_single_token = os.getenv("API_TOKEN", "").strip()
if _single_token:
    API_TOKENS.append(_single_token)

# Configuration Photos (chemin relatif au projet)
BASE_DIR = Path(__file__).parent.parent
PHOTO_DIR = Path(os.getenv("PHOTO_DIR", str(BASE_DIR / "camera_motion" / "photos")))

# Types de capteurs valides
VALID_SENSORS = ['temperature', 'humidity', 'light', 'distance', 'motion']

# États valides pour alarme/buzzer
VALID_STATES = ['ON', 'OFF']

# Limites
MAX_HISTORY_LIMIT = 1000
MIN_HISTORY_LIMIT = 1


def _extract_api_token():
    """Extrait le token depuis les headers ou query params"""
    # Priorité 1: Authorization Bearer (recommandé)
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    # Priorité 2: X-API-KEY header
    x_api_key = request.headers.get("X-API-KEY", "").strip()
    if x_api_key:
        return x_api_key

    # Priorité 3: Query parameter (moins sécurisé, mais supporté)
    token_qs = request.args.get("token", "").strip()
    if token_qs:
        logger.warning("Token utilisé via query parameter (moins sécurisé)")
        return token_qs

    return ""


def require_api_token(fn):
    """Décorateur pour exiger un token API valide"""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not API_TOKENS:
            logger.error("API token not configured")
            return jsonify({"error": "API token not configured"}), 500

        provided = _extract_api_token()
        if not provided:
            logger.warning(f"Tentative d'accès sans token: {request.remote_addr}")
            return jsonify({"error": "Unauthorized"}), 401

        # Comparaison sécurisée des tokens
        if not any(hmac.compare_digest(provided, t) for t in API_TOKENS):
            logger.warning(f"Token invalide depuis {request.remote_addr}")
            return jsonify({"error": "Unauthorized"}), 401

        return fn(*args, **kwargs)

    return wrapper


def get_db():
    """Obtient une connexion à la base de données avec gestion d'erreurs"""
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
    except pymysql.Error as e:
        logger.error(f"Erreur de connexion DB: {e}")
        raise


def validate_sensor(sensor):
    """Valide que le type de capteur est valide"""
    if sensor not in VALID_SENSORS:
        raise ValueError(f"Capteur invalide: {sensor}. Valides: {', '.join(VALID_SENSORS)}")
    return sensor


def validate_state(state):
    """Valide que l'état est valide"""
    state_upper = state.upper()
    if state_upper not in VALID_STATES:
        raise ValueError(f"État invalide: {state}. Valides: {', '.join(VALID_STATES)}")
    return state_upper


def safe_filename(filename):
    """Sécurise le nom de fichier pour éviter path traversal"""
    # Normaliser le chemin
    path = Path(filename)
    # Ne garder que le nom de fichier (pas de répertoires)
    safe_name = path.name
    # Vérifier que c'est un .jpg
    if not safe_name.endswith('.jpg'):
        raise ValueError("Seuls les fichiers .jpg sont autorisés")
    # Vérifier qu'il n'y a pas de caractères dangereux
    if '..' in safe_name or '/' in safe_name or '\\' in safe_name:
        raise ValueError("Nom de fichier invalide")
    return safe_name


# ========== DASHBOARD WEB ==========
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erreur rendu template: {e}")
        return jsonify({"error": "Template not found"}), 404


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de santé (sans authentification)"""
    db_status = "unknown"
    try:
        conn = get_db()
        conn.close()
        db_status = "ok"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_status = "error"
    
    return jsonify({
        "status": "ok",
        "database": db_status,
        "tokens_configured": len(API_TOKENS) > 0
    })


# ========== API ENDPOINTS ==========
@app.route('/api/dashboard', methods=['GET'])
@require_api_token
def dashboard():
    """Récupère les dernières valeurs de tous les capteurs"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        result = {}
        for sensor in VALID_SENSORS:
            try:
                cursor.execute(
                    "SELECT value, timestamp FROM sensor_data WHERE sensor_type=%s ORDER BY timestamp DESC LIMIT 1",
                    (sensor,)
                )
                row = cursor.fetchone()
                result[sensor] = row if row else None
            except pymysql.Error as e:
                logger.error(f"Erreur requête capteur {sensor}: {e}")
                result[sensor] = None
        
        return jsonify(result)
    except pymysql.Error as e:
        logger.error(f"Erreur DB dashboard: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logger.error(f"Erreur inattendue dashboard: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/alarm', methods=['POST'])
@require_api_token
def alarm_control():
    """Contrôle l'alarme via MQTT"""
    try:
        data = request.get_json() or {}
        state = validate_state(data.get('state', 'OFF'))
        
        publish.single(
            "server-room/alarm/cmd",
            payload=state,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={'username': MQTT_USER, 'password': MQTT_PASS},
            qos=1
        )
        logger.info(f"Alarme commandée: {state}")
        return jsonify({"status": "ok", "alarm": state})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur contrôle alarme: {e}")
        return jsonify({"status": "error", "message": "MQTT error"}), 500


@app.route('/api/buzzer', methods=['POST'])
@require_api_token
def buzzer_control():
    """Contrôle le buzzer via MQTT"""
    try:
        data = request.get_json() or {}
        state = validate_state(data.get('state', 'OFF'))
        
        publish.single(
            "server-room/buzzer/cmd",
            payload=state,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={'username': MQTT_USER, 'password': MQTT_PASS},
            qos=1
        )
        logger.info(f"Buzzer commandé: {state}")
        return jsonify({"status": "ok", "buzzer": state})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur contrôle buzzer: {e}")
        return jsonify({"status": "error", "message": "MQTT error"}), 500


@app.route('/api/history/<sensor>', methods=['GET'])
@require_api_token
def history(sensor):
    """Récupère l'historique d'un capteur"""
    conn = None
    cursor = None
    try:
        # Valider le capteur
        sensor = validate_sensor(sensor)
        
        # Valider et limiter le paramètre limit
        limit = request.args.get('limit', 100, type=int)
        if limit < MIN_HISTORY_LIMIT:
            limit = MIN_HISTORY_LIMIT
        elif limit > MAX_HISTORY_LIMIT:
            limit = MAX_HISTORY_LIMIT
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value, timestamp FROM sensor_data WHERE sensor_type=%s ORDER BY timestamp DESC LIMIT %s",
            (sensor, limit)
        )
        rows = cursor.fetchall()
        
        return jsonify(rows)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except pymysql.Error as e:
        logger.error(f"Erreur DB history: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logger.error(f"Erreur inattendue history: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ========== ENDPOINTS PHOTOS ==========
@app.route('/api/photos', methods=['GET'])
@require_api_token
def list_photos():
    """Retourne les 3 dernières photos"""
    try:
        if not PHOTO_DIR.exists():
            return jsonify([])
        
        # Lister tous les fichiers .jpg
        photos = [f for f in PHOTO_DIR.iterdir() if f.is_file() and f.suffix.lower() == '.jpg']
        
        # Trier par date de modification (plus récent d'abord)
        photos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Prendre les 3 dernières
        recent_photos = photos[:3]
        
        # Retourner avec timestamp
        result = []
        for photo in recent_photos:
            result.append({
                'filename': photo.name,
                'timestamp': photo.stat().st_mtime,
                'url': f'/api/photo/{photo.name}'
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur list_photos: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/photo/<filename>', methods=['GET'])
@require_api_token
def get_photo(filename):
    """Sert une photo spécifique avec protection path traversal"""
    try:
        # Sécuriser le nom de fichier
        safe_name = safe_filename(filename)
        filepath = PHOTO_DIR / safe_name
        
        if filepath.exists() and filepath.is_file():
            return send_file(str(filepath), mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Photo not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur get_photo: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ========== GESTION D'ERREURS GLOBALE ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur serveur: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Vérifier la configuration
    if not API_TOKENS:
        logger.warning("Aucun token API configuré! Utilisez API_TOKEN ou API_TOKENS")
    
    logger.info(f"API démarrée sur 0.0.0.0:5000")
    logger.info(f"Tokens configurés: {len(API_TOKENS)}")
    logger.info(f"Photo directory: {PHOTO_DIR}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
