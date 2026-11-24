# Guía de trabajo – Laboratorio 5 (no es parte de la entrega)

Esta guía indica qué ejecutar, qué capturar y qué conceptos usar en cada pregunta. Las respuestas del informe deben salir de **sus propias mediciones**: lo que aquí aparece como "esperable" es una hipótesis que deben confirmar o refutar con su evidencia.

---

## 0. Antes de empezar

1. Ejecuten `python3 lab5_simulacion.py --dry-run`. El resultado muestra N, el exponente, el rango de cada AP, los canales y **qué zonas de cobertura atraviesa cada estación y en qué segundo**. Sirve para planificar en qué momento medir y como tabla para el informe.
2. Graben la pantalla desde el inicio (OBS o la grabadora de la VM). El video lo pide la pregunta 1.
3. Los tiempos de movilidad empiezan en `t0` = 15 s (configurable con `--t0`). En ese intervalo converge STP. Los tiempos del *dry-run* son relativos a `t0`.
4. Entre ejecuciones: `exit` y después `sudo mn -c`.

Comandos útiles dentro de la CLI:

| Comando | Para qué |
|---|---|
| `sta3 iw dev sta3-wlan0 link` | AP asociado (BSSID, SSID), señal (dBm), tasa |
| `sta3 iw dev sta3-wlan0 station dump` | estadísticas del enlace (paquetes, reintentos) |
| `sh ovs-appctl stp/show ap1` | rol y estado de cada puerto STP (root, designated, blocking) |
| `sh ovs-appctl fdb/show ap0` | tabla MAC aprendida por el AP (por qué puerto sale cada estación) |
| `distance sta2 ap0` | distancia actual entre dos nodos |
| `links` / `net` | estado de los enlaces / topología |

### Datos del grupo 14 (cálculo teórico, confírmenlo en la simulación)

- N = 8: `ap0` central; lóbulo izquierdo `ap1`–`ap4`, lóbulo derecho `ap5`–`ap7`. Los adyacentes al central son `ap1`, `ap4`, `ap5` y `ap7`.
- Exponente 3,9; rango ≈ 83 m por AP (hay mucho solapamiento entre celdas).
- Tiempos absolutos (t0 = 15 s):
  - **sta2** (−212,0) → (229,0), t = 15–55 s: sin cobertura hasta ~17 s; pasa por ap2/ap3, entra a la zona de ap0 cerca de los 27 s y sale de toda cobertura cerca de los 54 s.
  - **sta3** (−61,43) → (61,−43), t = 15–60 s: siempre dentro del rango de ap0; cruza el origen cerca de los 37 s.
  - **sta4** (0,0) → (63,−5), t = 15–35 s. **sta5** x = −23, y de −94 a 94, t = 15–85 s: solo ap1 → ap0+ap1 (~20 s) → ap0+ap1+ap4 (~34 s) → ap0+ap4 (~66 s) → solo ap4 (~80 s).
- Pregunta 2, `link down`: el enlace pedido es `link ap0 ap1 down`. El camino alternativo es ap1 → ap2 → ap3 → ap4 → ap0.
- Pregunta 4: sta2 y sta3 comparten la cobertura de ap0 aproximadamente entre los 27 y los 52 s. Lancen iperf alrededor de los 33 s, cuando ambas están cerca del origen.

---

## Pregunta 1 – Código y video

Expliquen el script por bloques, sin copiar el README tal cual:

- **Cálculo de la topología** (clase `Topologia`): cómo se obtienen N y el exponente desde G, cómo se arman los dos anillos que comparten `ap0` y cómo se asignan los canales.
- **Rango de cobertura**: la fórmula de `logDistance` de Mininet-WiFi.
  `RSSI(d) = Pt + Gt + Gr − PL(1 m) − 10·n·log10(d)`. El rango es la distancia donde el RSSI llega a −91 dBm. Muestren el valor para su n.
- **STP**: por qué hace falta (ciclos → tormentas de broadcast y tablas MAC inestables), por qué `ap0` es la raíz y por qué se acortaron los temporizadores.
- **Movilidad**: `startMobility`, `mobility(start/stop)`, `stopMobility`, y cómo cada ruta cumple el enunciado (apóyense en la salida del *dry-run*).

Video sugerido (5–8 min): ejecución, plano con las estaciones moviéndose, un ping durante un traspaso, `iw link` de sta3, el `link down` y una medición con iperf.

---

## Pregunta 2 – Ping entre pares y falla de enlace

**Pares sugeridos**

- Par A (lóbulos distintos): **sta1 – sta4**. sta1 está fija en el lóbulo izquierdo y sta4 termina en el lóbulo derecho.
- Par B: **sta2 – sta3**. Ambas se mueven y cruzan los dos lóbulos, así que hay más traspasos para observar.

**Procedimiento** (una ejecución completa por par)

```
mininet-wifi> sta1 ping -i 0.2 sta4
```

Dejen correr el ping hasta que termine la movilidad (~t0+70 s) y deténganlo con Ctrl+C para obtener el resumen (% de pérdida, RTT mín/prom/máx). Anoten los `icmp_seq` en los que hay saltos y conviértanlos a tiempo (seq × 0,2 s) para cruzarlos con la tabla de zonas del *dry-run*.

**Qué buscar y cómo explicarlo**

- Pérdidas cuando una estación está fuera de toda cobertura (inicio y final de sta2).
- Pérdidas o picos de RTT en cada **traspaso**. El script cambia de AP cuando otro lo supera en 3 dB, o cuando la estación sale de cobertura. Cada cambio implica desasociarse y volver a asociarse (*break-before-make*), lo que deja un intervalo breve sin enlace. Los eventos quedan en `registros/traspasos_*.log`.
- Después del traspaso, los switches/APs del backbone siguen teniendo la MAC de la estación apuntando al puerto antiguo hasta que reaprenden. Comparen `fdb/show` antes y después. Kurose y Ross describen el mecanismo: el nuevo AP envía una trama broadcast con la MAC de la estación para que los switches se actualicen.
- Relación con la señal: menor RSSI → menor SNR → mayor BER, retransmisiones y adaptación de tasa a valores menores.

**Falla de enlace (par A)**

Esperen a que sta1 y sta4 estén quietas (después de t0+20 s), dejen el ping corriendo y ejecuten:

```
mininet-wifi> link ap0 ap1 down
mininet-wifi> sh ovs-appctl stp/show ap1
```

- Midan cuánto dura la interrupción. Corresponde a la reconvergencia de STP: el puerto que estaba bloqueado en el anillo izquierdo pasa por *listening/learning* (2 × forward-delay ≈ 8 s con la configuración del script).
- Camino alternativo: el anillo izquierdo se recorre en sentido contrario (ap1 → ap2 → … → último nodo del lóbulo → ap0). Muéstrenlo con `stp/show` y `fdb/show`.
- Si `ap0` deja de funcionar, es un **punto único de falla**: es el único nodo que une los dos lóbulos (un vértice de corte del grafo). Los lóbulos quedan aislados entre sí y, además, se pierde la cobertura inalámbrica del centro. Pueden demostrarlo bajando los cuatro enlaces de ap0.

---

## Pregunta 3 – Seguimiento del AP de sta3

**Procedimiento**: en la CLI, ejecuten `sta3 iw dev sta3-wlan0 link` cada 5 s (y en otra ejecución cada 3 s) con un cronómetro. Como respaldo, el script puede registrarlo automáticamente:

```
sudo python3 lab5_simulacion.py --monitor sta3 --cada 5
mininet-wifi> sh ls registros/   # después: cat registros/sta3_cada5.0s_*.log
```

Armen una tabla con: tiempo, SSID/BSSID, señal (dBm), tasa (tx bitrate). La fuente de verdad es `iw`, que muestra la asociación real del kernel; los atributos internos de Mininet-WiFi (`py sta3.wintfs[0]...`) solo sirven de apoyo. Comparen la señal medida con la teórica de la fórmula de la pregunta 1.

**Qué buscar**

- La secuencia de APs y si sta3 pasa por `ap0` o salta directo de un lóbulo al otro. Esto depende de su G. Contrasten con la columna de zonas del *dry-run*: que una estación esté dentro del rango de ap0 no significa que se asocie a él: solo se cambia a ap0 si su señal supera a la del AP actual en 3 dB.
- Con muestreo cada 5 s se pueden perder asociaciones cortas o desconexiones breves, que el muestreo cada 3 s sí detecta. Discutan la resolución temporal.
- La señal decae logarítmicamente con la distancia al AP y salta al asociarse a uno nuevo.
- Opcional: repitan con `--histeresis 0` y comparen. Sin histéresis, la estación puede saltar varias veces entre dos AP de señal parecida (efecto *ping-pong*).

**Escaneo activo**: describan las etapas usando sus observaciones como ejemplo.

1. La señal del AP actual cae; en una red real hay pérdida de beacons o se supera un umbral de RSSI.
2. La estación envía *Probe Request* en cada canal y los APs responden *Probe Response*.
3. La estación elige un AP y envía *Authentication* + *(Re)Association Request*; el AP responde con *Association Response*.
4. El backbone se actualiza para que el tráfico llegue por el nuevo AP.

Contrasten con el escaneo pasivo (escuchar beacons). Expliquen también que Mininet-WiFi, por defecto, **no** emula el escaneo real, sino que reasocia según la distancia o el rango. Por eso la pregunta dice "suponga".

---

## Pregunta 4 – sta2 por 3 zonas y throughput según canales

- **3 zonas**: la salida del *dry-run* muestra los APs que cubren cada tramo de sta2 (son más de 3 para cualquier G). Documenten esa tabla. Si cambian la ruta, expliquen por qué.
- **Cobertura compartida sta2/sta3**: ambas cruzan el origen cerca de t0+20 a t0+23 s, así que comparten la cobertura de ap0 en ese intervalo. Si para su G no coinciden lo suficiente, ajusten `t0` de una de ellas o la duración y documenten el cambio.

**Medición** (con `--interferencia`; sin wmediumd el canal prácticamente no influye en el emulador)

```
sudo python3 lab5_simulacion.py --interferencia --canales igual   # luego 456 y 1611
mininet-wifi> sta3 iperf -s &
mininet-wifi> sta2 iperf -c 10.0.0.3 -t 10 -i 1     # lanzar ~t0+17 s
```

(o simplemente `iperf sta2 sta3`). Repitan cada configuración al menos 3 veces y reporten promedio y desviación, porque la movilidad introduce variabilidad. Anoten a qué AP estaba asociada cada estación durante la medición (`iw link`): si ambas están en el mismo AP, el tráfico cruza el aire dos veces.

**Marco teórico para comparar**

- En 2,4 GHz los canales están separados por 5 MHz, pero cada canal ocupa ~20–22 MHz. Solo 1, 6 y 11 no se solapan.
- *Mismo canal*: todos los APs comparten el medio. CSMA/CA hace que se turnen (contienda, backoff, colisiones), así que el throughput se reparte.
- *4/5/6*: canales parcialmente solapados. La energía del canal vecino se percibe como ruido que no se puede decodificar, por lo que CSMA/CA no la coordina. En la práctica suele ser igual o peor que el mismo canal.
- *1/6/11*: sin solapamiento, cada celda usa su propio espectro → el mejor rendimiento esperado.
- Contrasten lo esperado con lo medido. Si el emulador no reproduce la diferencia (wmediumd modela la interferencia por SNR entre radios en la misma frecuencia, y el solapamiento entre canales adyacentes puede no estar modelado), díganlo y explíquenlo: es una limitación de la herramienta, no un error de su experimento. Verifiquen este punto en la documentación de wmediumd antes de afirmarlo.

---

## Referencias para revisar y citar

(Revisen que la numeración coincida con el "capítulo 6" de las clases del curso.)

- J. F. Kurose y K. W. Ross, *Computer Networking: A Top-Down Approach*, 8.ª ed., Pearson, 2021. Cap. 6 (capa de enlace, switches) y cap. 7 (redes inalámbricas y móviles: 802.11, escaneo activo/pasivo, movilidad en la misma subred).
- R. R. Fontes, S. Afzal, S. H. B. Brito, M. A. S. Santos y C. E. Rothenberg, "Mininet-WiFi: Emulating software-defined wireless networks", *CNSM 2015*.
- Repositorio y documentación de Mininet-WiFi: https://github.com/intrig-unicamp/mininet-wifi
- IEEE Std 802.1D-2004 (Spanning Tree) e IEEE Std 802.11-2020.
- Documentación de Open vSwitch, `ovs-vswitchd.conf.db(5)`: opciones `other_config:stp-*`.
