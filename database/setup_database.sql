-- Créer la base de données
CREATE DATABASE IF NOT EXISTS serverroom;
CREATE USER IF NOT EXISTS 'apiuser'@'localhost' IDENTIFIED BY 'apipass';
GRANT ALL PRIVILEGES ON serverroom.* TO 'apiuser'@'localhost';
FLUSH PRIVILEGES;
USE serverroom;

-- Créer la table
CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_type VARCHAR(50),
    value FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
