# Instalación de Mininet-WiFi

Hay dos opciones. La **VM del curso** es la más simple y no toca tu sistema. La **instalación nativa** es más cómoda y rápida, pero en versiones recientes de Ubuntu necesita algunos ajustes.

## Opción A – VM del curso (VirtualBox)

1. Instala VirtualBox (`sudo apt install virtualbox` en Ubuntu, o el instalador de virtualbox.org).
   - Con Secure Boot activado, VirtualBox pedirá crear una contraseña. Al reiniciar aparecerá la pantalla **MOK management**: elige *Enroll MOK* e ingresa esa contraseña.
   - Con procesador AMD y kernel reciente, si la VM no arranca (`VERR_SVM_IN_USE`), ejecuta `sudo modprobe -r kvm_amd kvm` antes de abrir VirtualBox.
2. Descarga el OVA desde el enlace del enunciado: https://drive.google.com/file/d/1R8n4thPwV2krFa6WNP0Eh05ZHZEdhw4W/view
3. Impórtalo (**Archivo → Importar servicio virtualizado**) con 2 CPU y 4 GB de RAM. Usuario y contraseña: `wifi` / `wifi`.
4. **Pasar archivos sin tipear:** en el equipo, ejecuta `cd entrega && python3 -m http.server 8000`. En la VM, el equipo se ve en la dirección `10.0.2.2`:
   ```bash
   wget http://10.0.2.2:8000/lab5_simulacion.py
   ```
   La prueba completa del script en la VM es una sola línea: `wget -qO- 10.0.2.2:8000/prueba_vm.sh | bash`. Para eso, `prueba_vm.sh` debe estar en la carpeta que se comparte.
5. **Portapapeles compartido (opcional):** *Dispositivos → Insertar imagen de CD de las Guest Additions*, luego `sudo sh /media/$USER/VBox*/VBoxLinuxAdditions.run`, reiniciar y activar *Dispositivos → Portapapeles compartido → Bidireccional*.

## Opción B – Instalación nativa en Ubuntu

Probada en Ubuntu 26.04 LTS (kernel 7.0, Python 3.14). En Ubuntu 22.04 o 24.04 los pasos especiales pueden no ser necesarios.

```bash
sudo apt update
sudo apt install -y git python3-tk python3-numpy
sudo modprobe mac80211_hwsim radios=2 && lsmod | grep hwsim && sudo modprobe -r mac80211_hwsim

cd ~
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
# Ubuntu 26.04: numpy<2 no existe para Python 3.14; se usa el numpy del sistema
sed -i 's/"numpy<2" //' util/install.sh
# Ubuntu 26.04: pip no puede reemplazar el certifi de apt; se instala uno aparte
sudo python3 -m pip install --break-system-packages --ignore-installed certifi
sudo python3 -m pip install --break-system-packages FlightRadarAPI bitstring skyfield

sudo util/install.sh -Wlnfv 2>&1 | tee ~/instalacion_mnwifi.log

# Dejar como "mn" el de Mininet-WiFi (no el de Mininet clásico)
sudo install -m 755 ~/mininet-wifi/bin/mn "$(which mn)"
```

Verificación (desde una carpeta distinta de `~/mininet-wifi`):

```bash
cd ~
sudo mn --wifi --test pingall        # debe terminar con "0% dropped"
python3 -c "import mn_wifi; print(mn_wifi.__file__)"
which wmediumd ovs-vsctl iperf iw
sudo mn -c
```

Notas:

- `linux-modules-extra-$(uname -r)` puede no existir: en Ubuntu 26.04 el módulo `mac80211_hwsim` ya viene en el kernel.
- El instalador agrega `openssh-server`. Si no lo usas: `sudo systemctl disable --now ssh.socket ssh.service`.
- Los archivos que genera el script quedan a nombre de root. Para borrarlos usa `sudo rm`, y para recuperarlos `sudo chown -R $USER:$USER registros`.
- Entre ejecuciones, limpia siempre con `sudo mn -c`.
