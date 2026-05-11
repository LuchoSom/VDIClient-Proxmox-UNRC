#!/bin/bash
# Configurar paquetes
sudo dpkg --configure -a
sudo apt install -y python3-pip python3-tk virt-viewer git
# Clonar el repositorio
git clone -b master https://github.com/LuchoSom/VDIClient-Proxmox-UNRC.git
cd VDIClient-Proxmox-UNRC
# Dar permisos de ejecución
chmod +x requirements.sh
# Actualizar e instalar dependencias
sudo apt update
sudo apt install -y python3-pip
sudo pip install PySimpleGUI==4.60.5
# Ejecutar el script de requisitos
./requirements.sh
# Copiar archivos y dar permisos
sudo cp vdiclientsom.py /usr/local/bin
sudo chmod +x /usr/local/bin/vdiclientsom.py
# Crear el directorio de configuración
sudo mkdir -p /etc/vdiclient
sudo cp vdiclient.ini /etc/vdiclient
# Agregar entradas a /etc/hosts
echo "192.168.1.225 masternode.lan" | sudo tee -a /etc/hosts
echo "192.168.1.240 nodo2.lan" | sudo tee -a /etc/hosts
echo "192.168.1.208 nodo3.lan" | sudo tee -a /etc/hosts
# Dar permisos de ejecución al script
sudo chmod +x /usr/local/bin/vdiclientsom.py