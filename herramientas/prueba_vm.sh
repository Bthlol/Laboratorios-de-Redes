#!/bin/bash
# Prueba del Laboratorio 5 en la VM del curso.
# Uso (dentro de la VM, con "python3 -m http.server 8000" corriendo en el equipo):
#   wget -qO- 10.0.2.2:8000/prueba_vm.sh | bash
# Deja todo el detalle en ~/lab5/prueba_vm.log y muestra un resumen al final.

SERVIDOR=10.0.2.2:8000
mkdir -p ~/lab5 && cd ~/lab5 || exit 1
LOG=~/lab5/prueba_vm.log
: > "$LOG"

echo "== Descargando archivos"
for f in lab5_simulacion.py medir_p4.sh README.md; do
  wget -q "http://$SERVIDOR/$f" -O "$f" || { echo "ERROR: no se pudo descargar $f"; exit 1; }
done

echo "== Pidiendo contrasena de sudo (es: wifi)"
sudo -v || exit 1

{
  echo "##### Versiones"
  lsb_release -ds 2>/dev/null
  python3 --version
  python3 -c "import mn_wifi, os; print('mn_wifi en', os.path.dirname(mn_wifi.__file__))"
  which wmediumd ovs-vsctl iperf iw
  echo "##### dry-run"
  python3 lab5_simulacion.py --dry-run
} >> "$LOG" 2>&1

echo "== Simulacion de prueba (unos 80 s, no escribas nada)"
sudo rm -rf registros
sudo mn -c >> "$LOG" 2>&1
sudo python3 lab5_simulacion.py --interferencia --monitor sta3 --cada 1 \
     --iperf 34.5 --iperf-dur 4 --duracion 70 --sin-grafico >> "$LOG" 2>&1
sudo mn -c >> "$LOG" 2>&1
sudo chown -R "$USER:$USER" registros 2>/dev/null

clear
echo "================ RESUMEN PRUEBA VM ================"
lsb_release -ds 2>/dev/null; python3 --version
grep -m1 "mn_wifi en" "$LOG"
echo "--- Problemas en la ejecucion (vacio = ninguno):"
grep -E "AVISO|Traceback|Error|Exception" "$LOG" | head -n 8
grep -h "error con" registros/traspasos_*.log 2>/dev/null | head -n 5
echo "--- Traspasos de sta2 y sta3:"
grep -hE "sta[23] (traspaso|se asocia|pierde)" registros/traspasos_*.log 2>/dev/null
echo "--- AP de sta3 (registro cada 1 s):"
awk '/== t=/{t=$2} /SSID/{print t, $2} /Not connected/{print t, "--"}' \
    registros/sta3_cada1*.log 2>/dev/null | uniq -f1 | tr '\n' ' '; echo
echo "--- iperf sta2 -> sta3:"
grep -hE "sta[23]:|0.0000-[0-9.]+ sec" registros/iperf_*.txt 2>/dev/null | tail -n 5
echo "==================================================="
echo "Detalle completo en ~/lab5/prueba_vm.log"
