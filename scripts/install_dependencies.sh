#!/bin/bash

# Script d'installation des dépendances pour le système IoT Server Room
# Usage: sudo ./install_dependencies.sh

echo "=== Installation des dépendances système ==="
apt update && apt upgrade -y
apt install -y mariadb-server mosquitto mosquitto-clients python3-pip

echo ""
echo "=== Installation des dépendances Python pour mqtt_logger ==="
cd ~/mqtt_logger
pip3 install -r requirements.txt

echo ""
echo "=== Installation des dépendances Python pour api_rest ==="
cd ~/api_rest
pip3 install -r requirements.txt

echo ""
echo "=== Installation des dépendances Python pour dashboard ==="
cd ~/dashboard
pip3 install -r requirements.txt

echo ""
echo "=== Installation terminée ==="
echo "Prochaines étapes:"
echo "1. Configurer MariaDB (voir README.md)"
echo "2. Configurer Mosquitto (voir README.md)"
echo "3. Copier les fichiers de service systemd"
echo "4. Démarrer les services"
