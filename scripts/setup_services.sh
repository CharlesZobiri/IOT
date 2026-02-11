#!/bin/bash

# Script de configuration des services systemd
# Usage: sudo ./setup_services.sh

echo "=== Copie des fichiers de service systemd ==="
cp ../systemd/mqtt-logger.service /etc/systemd/system/
cp ../systemd/api-rest.service /etc/systemd/system/

echo ""
echo "=== Rechargement de systemd ==="
systemctl daemon-reload

echo ""
echo "=== Activation des services ==="
systemctl enable mqtt-logger
systemctl enable api-rest

echo ""
echo "=== Services configurés ==="
echo "Pour démarrer les services:"
echo "  sudo systemctl start mqtt-logger"
echo "  sudo systemctl start api-rest"
echo ""
echo "Pour vérifier le statut:"
echo "  sudo systemctl status mqtt-logger"
echo "  sudo systemctl status api-rest"
