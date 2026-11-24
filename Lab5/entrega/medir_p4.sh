#!/bin/bash
# Pregunta 4: throughput sta2 -> sta3 con tres configuraciones de canales,
# 3 repeticiones cada una. Cada ejecucion dura ~1 minuto (unos 10 min en total).
# Uso: bash medir_p4.sh
cd "$(dirname "$0")"
sudo -v || exit 1
for canales in igual 456 1611; do
  for rep in 1 2 3; do
    echo "===== canales=$canales repeticion=$rep ====="
    sudo mn -c > /dev/null 2>&1
    sudo python3 lab5_simulacion.py --interferencia --canales "$canales" \
         --iperf 34.5 --iperf-dur 4 --duracion 45 --sin-grafico 2>&1 \
         | grep -E "iperf|Eventos|Error|Traceback"
    sleep 2
  done
done
sudo mn -c > /dev/null 2>&1
sudo chown -R "$USER:$USER" registros
echo "Listo. Resultados en registros/iperf_*.txt"
