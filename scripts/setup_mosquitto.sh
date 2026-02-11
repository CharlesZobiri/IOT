#!/bin/bash

# Script de configuration de Mosquitto
# Usage: sudo ./setup_mosquitto.sh

echo "=== Configuration de Mosquitto ==="

echo ""
echo "=== Copie du fichier de configuration ==="
cp ../mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf

echo ""
echo "=== Copie de l'ACL ==="
cp ../mosquitto/acl /etc/mosquitto/acl

echo ""
echo "=== Création des utilisateurs MQTT ==="
mosquitto_passwd -c /etc/mosquitto/passwd admin
mosquitto_passwd -b /etc/mosquitto/passwd esp32 esp32pass
mosquitto_passwd -b /etc/mosquitto/passwd arduino arduinopass
mosquitto_passwd -b /etc/mosquitto/passwd dashboard dashpass
mosquitto_passwd -b /etc/mosquitto/passwd logger logpass

echo ""
echo "=== Redémarrage de Mosquitto ==="
systemctl restart mosquitto
systemctl enable mosquitto

echo ""
echo "=== Vérification du statut ==="
systemctl status mosquitto

echo ""
echo "=== Configuration terminée ==="
echo "Pour tester la connexion:"
echo "  mosquitto_sub -h localhost -p 1883 -u admin -P adminpass -t '#' -v"
