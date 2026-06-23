#!/bin/bash

# Wazuh All-in-One Installer Script for Ubuntu 20.04/22.04
# Includes Wazuh Manager, Dashboard, Filebeat, and Elasticsearch

echo "[+] Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "[+] Installing curl and dependencies..."
sudo apt install -y curl apt-transport-https lsb-release gnupg

echo "[+] Downloading Wazuh installation script..."
curl -sO https://packages.wazuh.com/4.7/wazuh-install.sh

echo "[+] Making script executable..."
chmod +x wazuh-install.sh

echo "[+] Running Wazuh installer (all-in-one)..."
sudo bash wazuh-install.sh -a

echo ""
echo "[✔] Wazuh installation complete!"
echo "Access the Wazuh Dashboard at: https://<your-server-ip>"
echo "Default credentials: admin / admin"