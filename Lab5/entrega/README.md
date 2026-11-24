# Laboratorio 5 – Redes de Computadores (Mininet-WiFi)

## Integrantes

| Nombre | Rol USM |
|---|---|
| Benjamín Torres | 202373539-6 |
| _(completar)_ | _(completar)_ |
| _(completar)_ | _(completar)_ |

Grupo: **14** → N = 6 + (14 mod 4) = 8 nodos, exponente de pérdida = 3.5 + 4/10 = 3.9 (rango de cobertura ≈ 83 m).

## Requisitos

- Máquina virtual de Mininet-WiFi (OVA del curso) o instalación manual desde el repositorio oficial.
- Python 3, Open vSwitch y, para la pregunta 4, `wmediumd` (incluido en la VM).

## Ejecución

```bash
sudo python3 lab5_simulacion.py -g
```

Antes de ejecutar, se puede revisar la topología calculada (posiciones, rangos, canales y zonas de cobertura que recorre cada estación) sin Mininet:

```bash
python3 lab5_simulacion.py -g --dry-run
```

Si una ejecución anterior terminó mal, limpiar con `sudo mn -c` antes de volver a ejecutar.

### Opciones

| Opción | Descripción |
|---|---|
| `-g, --grupo G` | Número de grupo (por defecto 14). Define N = 6 + (G mod 4) y el exponente 3.5 + X/10. |
| `--t0 S` | Segundos de espera antes de iniciar la movilidad (por defecto 15) para que STP converja. |
| `--canales base\|igual\|456\|1611` | Canales del nodo central y sus 4 adyacentes (pregunta 4). |
| `--interferencia` | Usa wmediumd en modo interferencia (necesario para que el canal influya). |
| `--histeresis DB` | Margen en dB que debe superar otro AP para que la estación cambie de AP (por defecto 3). |
| `--monitor sta3 --cada 5` | Registra `iw dev sta3-wlan0 link` cada 5 s (acepta varias estaciones: `--monitor sta1,sta4`) en `registros/` (dentro de la carpeta del laboratorio; un archivo por ejecución). |
| `--iperf T` / `--iperf-dur S` | Mide el throughput sta2 → sta3 con iperf desde t = T s durante S s (por defecto 4 s) y guarda el resultado en `registros/iperf_<canales>_HHMMSS.txt`. |
| `--duracion S` | Ejecuta la simulación S segundos sin abrir la CLI y la detiene sola. |
| `--sin-grafico` | No abre la ventana del plano. |

### Comandos por pregunta

```bash
# P2: ping constante entre un par (una ejecución por par)
sudo python3 lab5_simulacion.py
mininet-wifi> sta2 ping -i 0.2 sta3
# P2: falla de un enlace del nodo central
mininet-wifi> link ap0 ap1 down

# P3: datos del AP de sta3 cada 5 s y luego cada 3 s
mininet-wifi> sta3 iw dev sta3-wlan0 link
sudo python3 lab5_simulacion.py --monitor sta3 --cada 5
sudo python3 lab5_simulacion.py --monitor sta3 --cada 3

# P4: throughput entre sta2 y sta3 (ambas asociadas a ap0 entre t≈34,5 y 39 s),
#     3 configuraciones de canales x 3 repeticiones, automatico (~10 min)
bash medir_p4.sh
```

## Decisiones de implementación

- **Nombres**: `ap0` es el nodo central en (0,0,0); luego se numeran los nodos del lóbulo izquierdo y después los del derecho, siguiendo el orden de la tabla del enunciado.
- **Ciclos y STP**: cada lóbulo es un anillo, así que los APs usan `failMode='standalone'` y `stp=True` sin controlador. `ap0` tiene prioridad de puente 4096 para que sea la raíz, y los temporizadores STP se acortaron (hello 1 s, max-age 6 s, forward-delay 4 s) para que la red converja en unos 8 s en vez de unos 30 s.
- **Cobertura**: se usa el modelo `logDistance` con exponente 3.5 + X/10. El rango se estima con los valores por defecto de Mininet-WiFi (14 dBm, ganancia 5 dBi, umbral −91 dBm). Con ese rango se calculan los extremos de la ruta de `sta2`, para que parta y termine fuera de cobertura, y los de `sta5`, para que entre a la zona de solapamiento y salga de ella.
- **Control de asociación y traspaso**: el control de Mininet-WiFi se desactivó (`allAutoAssociation=False`) porque en esta topología no era confiable: asociaba al primer AP de la lista, dejaba el registro interno distinto de la asociación real y algunas estaciones no se volvían a asociar. Lo reemplaza la clase `ControlTraspaso`. Cada 0,5 s calcula el RSSI de cada estación a cada AP con el modelo log-distance. Si la estación sale de la cobertura de su AP, se desconecta y se asocia al de mejor señal. Si otro AP supera al actual en al menos 3 dB (histéresis), hace un traspaso desconectándose primero (*break-before-make*). Cada evento se registra en `registros/traspasos_HHMMSS.log`.
- **Altura de las estaciones**: las estaciones están a 1 m de altura (z = 1). Sus coordenadas (x, y) son exactamente las del enunciado. wmediumd calcula la pérdida con log10(d) y no admite distancia 0, que se daba con sta4 al partir sobre ap0 y con sta3 al terminar sobre ap5.
- **Estaciones**: `sta1` está fija en el interior del lóbulo izquierdo. `sta2` recorre el eje X en 40 s. `sta3` va en línea recta por el origen hasta el nodo inferior del lóbulo derecho en 45 s. `sta4` va del origen al interior del lóbulo derecho en 20 s. `sta5` recorre el eje Y entre el nodo central y sus adyacentes izquierdos en 70 s. La ruta de sta5 se interpretó como un desplazamiento en la dirección del eje Y, sobre la recta x = −23, entre ap0 y sus adyacentes izquierdos.
