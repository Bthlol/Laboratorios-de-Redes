# Borrador del informe – Laboratorio 5 (Grupo 14)

> Borrador de trabajo. Reescríbelo con tus palabras antes de pasarlo al PDF y agrega las capturas indicadas.
> Todos los datos vienen de las ejecuciones del 23/11 con `--interferencia`.

---

## Pregunta 1 – Implementación y funcionamiento

**Video:** *(pegar aquí el enlace; por ejemplo YouTube no listado o Google Drive con acceso para cualquiera con el enlace)*

El archivo `lab5_simulacion.py` implementa la simulación con la API de Python de Mininet-WiFi. Se ejecuta con `sudo python3 lab5_simulacion.py [opciones]`. Las opciones, explicadas en el README, permiten activar el modo de interferencia, cambiar los canales, registrar la asociación de una estación, medir throughput o ejecutar sin CLI. Con `--dry-run` imprime la topología calculada sin iniciar Mininet. El código se organiza en seis bloques.

### 1.1 Parámetros del grupo y modelo de propagación

Con G = 14 se obtienen N = 6 + (14 mod 4) = **8 nodos** y X = 4. El exponente de pérdida es 3,5 + 4/10 = **3,9**. Las posiciones de los AP se toman de la tabla del enunciado (diccionario `TABLA`).

El modelo *log-distance* calcula la señal recibida a una distancia d:

RSSI(d) = P_t + G_t + G_r − PL(1 m) − 10·n·log₁₀(d)

Se usan los valores por defecto de Mininet-WiFi: P_t = 14 dBm y G = 5 dBi. PL(1 m) es la pérdida en espacio libre a 1 m, ≈ 40 dB en 2,4 GHz. La función `rango_logdistance` despeja la distancia en que la señal llega al umbral de −91 dBm, lo que da un **rango de ≈ 83 m** por AP. Con ese rango se calculan los extremos de las rutas de sta2 (que debe partir y terminar fuera de cobertura) y de sta5 (que debe entrar y salir de la zona de solapamiento).

### 1.2 Clase `Topologia`

Esta clase calcula toda la geometría, sin depender de Mininet:

- **Nodos:** `ap0` es el nodo central en (0, 0). Le siguen `ap1`–`ap4` (lóbulo izquierdo, con un nodo más por ser N par) y `ap5`–`ap7` (lóbulo derecho).
- **Enlaces cableados:** cada lóbulo es un anillo que empieza y termina en `ap0`. Así ap0 queda conectado a 4 nodos y el resto a sus 2 vecinos: ap0–ap1–ap2–ap3–ap4–ap0 y ap0–ap5–ap6–ap7–ap0.
- **Canales:** cada AP tiene un canal distinto entre 1 y 11. Las configuraciones de la P4 (`--canales igual|456|1611`) cambian solo ap0 y sus cuatro adyacentes, cuidando que AP vecinos no compartan canal.
- **Estaciones:**

| Estación | Movimiento | Cumplimiento del enunciado |
|---|---|---|
| sta1 | Fija en (−64, 5) | Interior del lóbulo izquierdo, sin coincidir con ningún AP |
| sta2 | (−212, 0) → (229, 0) en 40 s | Parte y termina fuera de cobertura, pasa por el nodo central y atraviesa los 8 AP |
| sta3 | (−61, 43) → (61, −43) en 45 s | Parte en la cobertura de ap4 (cuadrante superior izquierdo) y va en línea recta por el origen hasta ap5 (cuadrante inferior derecho) |
| sta4 | (0, 0) → (63, −5) en 20 s | Parte en el origen y llega al interior del lóbulo derecho, el contrario al de sta1 |
| sta5 | (−23, −94) → (−23, 94) en 70 s | Se mueve en la dirección del eje Y, entre ap0 y sus adyacentes izquierdos, y entra y sale de la zona de solapamiento (solo ap1 → ap0 + ap1 → ap0 + ap1 + ap4 → ap0 + ap4 → solo ap4) |

**Decisiones de interpretación:**

- "A lo largo del eje Y" (sta5) se interpretó como un desplazamiento en la dirección del eje Y. Se eligió la recta x = −23, a medio camino entre ap0 y sus adyacentes izquierdos (ap1 y ap4, en x = −46), porque ahí se ve con más claridad cómo la estación entra a la zona de solapamiento y sale de ella. En cambio, sta2 recorre exactamente el eje X (y = 0), porque además debe pasar por el nodo central.
- Las estaciones están a 1 m de altura (z = 1). Sus coordenadas (x, y) son las del enunciado; la razón se explica en la sección 1.3.

El método `zonas` recorre cada ruta e informa qué AP la cubren en cada tramo. Es lo que imprime `--dry-run`.

### 1.3 Construcción de la red (función `topology`)

1. **Puntos de acceso** (`addAccessPoint`): se crean con su SSID, canal y posición, y con `failMode='standalone'` y `stp=True`. Como los lóbulos son anillos, la red cableada tiene ciclos. Sin STP, las tramas de difusión circularían indefinidamente (tormenta de broadcast) y las tablas MAC serían inestables. Con `standalone` los AP funcionan como switches con aprendizaje, sin controlador OpenFlow.
2. **Estaciones** (`addStation`): se crean con MAC e IP fijas (10.0.0.1–5) y **1 m de altura**. Las coordenadas (x, y) son exactamente las del enunciado. La altura evita la distancia 0 entre sta4 y ap0 al inicio, y entre sta3 y ap5 al final, porque wmediumd calcula log₁₀(d) y no admite d = 0.
3. **Propagación** (`setPropagationModel(model='logDistance', exp=3.9)`), configuración de nodos y **enlaces cableados** (`addLink`) entre AP.
4. **Movilidad:** se usan `startMobility`, `mobility(sta, 'start'/'stop', time, position)` y `stopMobility`. Todas las estaciones móviles parten en t0 = 15 s, para que antes converja STP.
5. **Inicio** (`build`, `ap.start([])`) y **ajuste de STP:** `ap0` recibe la prioridad más alta (4096), para que sea la raíz del árbol. Se acortan los temporizadores (hello = 1 s, max-age = 6 s, forward-delay = 4 s). La red converge en ~8 s y una falla se recupera en ~14 s; con los valores por defecto serían ~30 s y ~50 s.

### 1.4 Control de traspaso (clase `ControlTraspaso`)

Mininet-WiFi trae su propio control de asociación, pero en esta topología mostró varios problemas:

- Asociaba cada estación al primer AP de la lista que la tuviera en rango, aunque estuviera en el borde de su cobertura.
- Al cambiar de AP no desconectaba primero, así que el kernel rechazaba la nueva conexión mientras la librería registraba el cambio.
- Algunas estaciones no volvían a asociarse tras perder la cobertura.

Por eso se desactivó (`allAutoAssociation=False`) y se reemplazó por un hilo propio. Cada 0,5 s y para cada estación:

1. Calcula la señal hacia cada AP en rango, con el mismo modelo *log-distance*.
2. Si la estación salió de la cobertura de su AP, la desconecta (`iw dev staX-wlan0 disconnect`).
3. Si no tiene AP, la asocia al de mejor señal (`iw dev staX-wlan0 connect <SSID> <BSSID>`).
4. Si otro AP supera al actual en **al menos 3 dB** (histéresis), hace el traspaso: primero se desconecta y luego se asocia al nuevo (*break-before-make*). La histéresis evita el efecto *ping-pong* entre AP de señal parecida.
5. Verifica con `iw dev staX-wlan0 link` que la asociación se haya completado. Si no ocurre en 3 s, la reintenta.

Cada evento queda en `registros/traspasos_HHMMSS.log`, con su tiempo, AP de origen y destino, y las señales. Ese registro es la evidencia principal de las preguntas 2, 3 y 4.

### 1.5 Instrumentación para las mediciones

- `--interferencia`: usa wmediumd en modo interferencia, en que la señal de cada trama depende de la posición de los nodos.
- `--monitor sta3 --cada 5`: ejecuta `iw dev sta3-wlan0 link` periódicamente y lo guarda en `registros/` (P3).
- `--iperf 34.5 --iperf-dur 4`: mide el throughput de sta2 a sta3 en el instante en que ambas comparten ap0, y guarda el resultado con el AP de cada estación (P4). El lote `medir_p4.sh` repite la medición 3 veces por configuración de canales.
- `--duracion S`: ejecuta sin CLI y se detiene sola.
- Al iniciar se imprime una **referencia de tiempo**, que permite convertir las marcas de `ping -D` al tiempo de la simulación (P2).

*(Capturas sugeridas: el plano de la topología con las estaciones en movimiento, la salida de `--dry-run` y un extracto del registro de traspasos.)*

---

## Pregunta 2 – Ping entre pares y falla de enlace

### 2.1 Ping continuo durante la movilidad

Se eligieron dos pares. En el **par A, sta1 → sta4**, sta1 está fija en el lóbulo izquierdo (ap4) y sta4 va del centro al lóbulo derecho. En el **par B, sta2 → sta3**, ambas estaciones se mueven y cruzan los dos lóbulos. Cada par se midió en una ejecución completa, con `ping -D -i 0.2`. Los tiempos se cruzaron con el registro de traspasos.

**Par A – sta1 → sta4** (397 enviados, 375 recibidos, **5,5 % de pérdida**, RTT promedio 1,7 ms):

| t (s) | Qué ocurre | Efecto en el ping |
|---|---|---|
| ~11 – 14,5 | Arranque: sta1 terminó de asociarse a ap4 en t = 9,9 y aún no hay resolución ARP de sta4 | seq 1–20: *Destination Host Unreachable* |
| 14,5 – 30,4 | sta4 se aleja de ap0 (−16 → −82 dBm) | Sin pérdidas; RTT de 1–3 ms con picos de 6–8 ms y dos de 57–63 ms |
| 30,4 – 31,0 | **Traspaso de sta4: ap0 → ap5** | seq 103–104 perdidos (~0,6 s) |
| 31,0 – 90 | Ambas quietas | Sin pérdidas |

**Par B – sta2 → sta3** (290 enviados, 95 recibidos, **67 % de pérdida**):

| t (s) | Qué ocurre | Efecto en el ping |
|---|---|---|
| ~12 – 21,7 | sta2 fuera de cobertura hasta t ≈ 17,5. Luego entra a ap2 con −91 dBm; el primer intento falla y se asocia en t = 21,7 | *Unreachable* |
| 21,8 – 28,3 | sta2 en ap2, sta3 en ap4 (mismo lóbulo) | Sin pérdidas, RTT ≈ 1 ms |
| 28,3 – 34,8 | **Traspasos casi simultáneos**: sta2 ap2 → ap4 (falla) → ap0 (t = 32,7); sta3 ap4 → ap0 (t = 34,3) | ~6,5 s sin servicio |
| 34,8 – 39,3 | Ambas asociadas a ap0 | Sin pérdidas |
| 39,3 – 43,5 | **Traspaso de sta2**: ap0 → ap5 (falla) → ap6 (t = 43,5) | ~4,2 s sin servicio; al volver, 5 respuestas llegan juntas con RTT 1013 → 184 ms |
| 43,5 – 50,2 | sta2 en ap6, sta3 en ap0 (lóbulos distintos) | Sin pérdidas; RTT de hasta 7,7 ms |
| 50,2 – fin | **Traspaso de sta3** ap0 → ap5 (t = 50,3–54,6). Antes de que termine, sta2 sale de la cobertura de ap6 (t = 54,0, x ≈ 217 m) | Sin servicio hasta el final |

**¿En qué momentos hay ralentización o pérdidas?**

- **Fuera de cobertura:** sta2 al inicio y al final de su recorrido.
- **En cada traspaso:** ~0,6 s en el mejor caso (sta4) y ~4 s cuando falla el primer intento de asociación. El peor caso es el par B, cuando ambas estaciones cambian de AP casi al mismo tiempo (~6,5 s).
- **Señal débil en el borde de una celda:** aparecen picos de RTT (6–63 ms) sin pérdidas.

**¿Hay interrupciones durante el desplazamiento?** Sí. En el par A hay solo una, breve, porque solo una estación se mueve y cambia de AP una vez. En el par B hay cuatro tramos sin servicio, porque ambas estaciones se mueven, sta2 entra y sale de cobertura, y sus traspasos coinciden con los de sta3.

**¿Por qué ocurre?**

1. **Traspaso *break-before-make*:** la estación se desasocia del AP anterior antes de asociarse al nuevo. Mientras tanto no puede enviar ni recibir tramas, y los paquetes de ese intervalo se pierden.
2. **Actualización de la red cableada y de ARP:** tras el traspaso, los switches deben reaprender por qué puerto se llega a la MAC de la estación. Si se perdió la entrada ARP, el emisor debe volver a resolverla. Mientras ARP no se resuelve, ping informa *Destination Host Unreachable* y encola los paquetes. Al resolverse salen todos juntos, por eso el RTT decrece de a ~200 ms (1013 → 184 ms), que es el intervalo de envío.
3. **Atenuación con la distancia:** al alejarse del AP baja la señal, y con ella la relación señal/ruido. Aumentan los errores de bits y las retransmisiones, y la estación usa tasas de transmisión menores. Eso explica los picos de RTT antes de cada traspaso.
4. **Fuera de cobertura:** bajo el umbral de recepción (−91 dBm) no hay enlace posible.

### 2.2 Falla del enlace ap0–ap4

sta1 está asociada a **ap4** y sta4 a **ap5**, ambas quietas. El enunciado pide desactivar un enlace del nodo central. Se eligió **ap0–ap4** porque es el enlace por el que pasa el tráfico de sta1 (el equivalente a ap0–ap1 en nuestro caso). Cortar ap0–ap1 no afecta a sta1: se verificó en una ejecución previa, con 0 % de pérdida.

**Estado de STP antes de la falla.** El árbol tiene raíz en ap0 (prioridad 4096). En el anillo izquierdo, el puerto `ap3-eth2` (enlace ap2–ap3) está en **blocking**. Así se corta el ciclo, y ap3 llega a la raíz por ap4 con costo 4.

**Resultado.** Ping con `-D -i 0.2`, convertido al tiempo de la simulación:

| Tramo | icmp_seq | t (s) | Resultado |
|---|---|---|---|
| Antes de la falla | 1–46 | 71,0 – 80,1 | Sin pérdidas, RTT ≈ 3,3 ms |
| `link ap0 ap4 down` | 47–107 | 80,1 – 92,9 | **61 paquetes perdidos (~12,9 s sin servicio)** |
| Después de la falla | 108–251 | 92,9 – 121 | Sin pérdidas, RTT ≈ 3,3 ms |
| **Total** | | | 251 enviados, 190 recibidos, 24,3 % de pérdida |

**Estado de STP después de la falla:**

- ap4: puerto raíz `ap4-eth2` (hacia ap3), costo 8.
- ap3: puerto raíz `ap3-eth2` (hacia ap2), costo 6. El puerto que estaba bloqueado pasó a *forwarding*.
- ap0: ya no aparece `ap0-eth3` (enlace caído).

**¿Se mantiene la comunicación?** Sí, después de una interrupción de ~13 s.

**¿Qué camino sigue el tráfico?** sta1 → ap4 → ap3 → ap2 → ap1 → ap0 → ap5 → sta4. Recorre el anillo izquierdo en sentido contrario y usa el enlace ap2–ap3, que antes estaba bloqueado. El costo de ap4 a la raíz subió de 2 a 8 (4 enlaces × 2). Aun así, el RTT casi no cambió (~3,3 ms), porque los enlaces cableados emulados tienen un retardo despreciable frente al tramo inalámbrico.

**¿Por qué tarda ~13 s?** STP (IEEE 802.1D) evita los ciclos bloqueando puertos redundantes. Cuando cae un enlace, el puerto bloqueado no puede pasar a reenviar de inmediato. Primero debe expirar la información almacenada del camino anterior (*max-age*). Luego el puerto pasa por los estados *listening* y *learning*, de *forward-delay* cada uno, antes de llegar a *forwarding*. Así se evita formar ciclos transitorios. Con la configuración usada (max-age = 6 s, forward-delay = 4 s), el tiempo esperado es 6 + 2·4 = **14 s**, coherente con los ~12,9 s medidos. Con los valores por defecto del estándar (20 s y 15 s) serían ~50 s. RSTP (802.1w) reduce este tiempo a pocos segundos o menos. Además, tras el cambio de topología los switches deben volver a aprender por qué puerto se llega a cada MAC.

**¿Qué ocurriría si el nodo central dejara de funcionar?** Se simuló desactivando los cuatro enlaces de ap0 (ap4, ap1, ap5 y ap7). El ping de sta1 a sta4 pasó de 10/10 recibidos a **0/10 (100 % de pérdida)**. ap0 es el único nodo que une ambos lóbulos: es un **punto único de falla** (un vértice de corte del grafo). Sin él, cada lóbulo sigue conectado internamente, porque es un anillo, pero no existe ningún camino entre los dos. STP no puede resolverlo, porque solo puede activar enlaces redundantes que existan, y no hay ninguno entre lóbulos. Además, las estaciones asociadas a ap0 pierden la conexión inalámbrica y deben reasociarse a otro AP si tienen alguno en rango. Para eliminar este punto de falla habría que agregar un enlace directo entre los lóbulos (por ejemplo ap1–ap5) o un segundo nodo central redundante.

*(Capturas sugeridas: `stp/show ap3` antes y después, `stp/show ap4` después, y el tramo del ping donde saltan los icmp_seq 46 → 108.)*

---

## Pregunta 3 – Punto de acceso de la estación 3

### Procedimiento

La simulación se ejecutó con el modo de interferencia de wmediumd (`--interferencia`). En ese modo, la señal que informa `iw` se calcula con el modelo *log-distance* según la posición de cada nodo. El punto de acceso de sta3 se consultó con `sta3 iw dev sta3-wlan0 link`, tanto a mano en la CLI de Mininet-WiFi como con un registro automático (`--monitor sta3 --cada S`) que ejecuta el mismo comando cada S segundos. Se hicieron dos ejecuciones, con S = 5 s y S = 3 s. Se agrega como referencia el registro cada 1 s de otra ejecución idéntica.

sta3 recorre en 45 s una línea recta desde (−61, 43) hasta la posición de ap5 en (61, −43), pasando por el origen. Las estaciones están a 1 m de altura. La asociación la decide el control de traspaso del script: la estación se cambia de AP cuando otro la supera en al menos 3 dB, o cuando sale de cobertura. Cada evento queda en `registros/traspasos_*.log`. Los tiempos se miden desde el inicio de la red, y sta3 empieza a moverse cerca de t ≈ 16 s.

*(Capturas sugeridas: las consultas manuales con `iw`, un extracto de cada registro y el archivo de traspasos.)*

### Resultados

Eventos registrados por el control de traspaso (iguales, ±0,3 s, en las cuatro ejecuciones):

| t (s) | Evento |
|---|---|
| 5,5 – 8,9 | sta3 se asocia a ap4 (−63 dBm) |
| 29,8 | Traspaso ap4 (−76 dBm) → ap0 (−71 dBm) |
| 33,2 – 34,3 | sta3 queda asociada a ap0 (el primer intento falló y se reintentó) |
| 50,1 – 50,5 | Traspaso ap0 (−79 dBm) → ap5 (−75 dBm) |
| 54,5 – 54,8 | sta3 queda asociada a ap5 (primer intento fallido y reintento) |

Registro con muestreo cada **5 s**:

| t (s) | 11 | 16 | 21 | 26 | 31 | 36 | 41 | 46 | 51 | 56 | 61 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AP | ap4 | ap4 | ap4 | ap4 | — | ap0 | ap0 | ap0 | — | ap5 | ap5 |
| dBm | −63 | −61 | −41 | −65 | — | −49 | −54 | −71 | — | −62 | −19 |

Registro con muestreo cada **3 s**:

| t (s) | 12 | 18 | 21 | 27 | 30 | 33 | 36 | 39 | 45 | 48 | 51 | 54 | 57 | 63 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AP | ap4 | ap4 | ap4 | ap4 | ap4 | — | ap0 | ap0 | ap0 | ap0 | — | — | ap5 | ap5 |
| dBm | −63 | −52 | −41 | −68 | −75 | — | −49 | −36 | −69 | −75 | — | — | −57 | −19 |

Registro de referencia cada **1 s**: ap4 entre t = 10 y 29 s (máximo −39 dBm en t = 20). Sin conexión en t = 30–33. ap0 entre t = 34 y 50 (máximo −24 dBm en t = 38). Sin conexión en t = 51–54. ap5 desde t = 55.

Consultas manuales en la CLI:

- Ejecución de 5 s: ap4 (−44 dBm), ap0 (−57 dBm), ap0 (−68 dBm).
- Ejecución de 3 s: ap4 (−43 dBm), ap0 (−54 dBm), *Not connected*, ap5 (−62 dBm).

### Respuestas

**¿Cambia el punto de acceso durante el desplazamiento?** Sí. En todas las ejecuciones sta3 pasó por tres AP y siempre en el mismo orden: ap4 (lóbulo izquierdo), ap0 (nodo central) y ap5 (lóbulo derecho).

**¿Ocurren desconexiones?** Sí, dos: una en cada traspaso. El registro de 1 s muestra unos 4 s sin conexión en cada una (t = 30–33 y t = 51–54). La estación primero se desconecta del AP anterior y después se asocia al nuevo (*break-before-make*). En el emulador, buena parte de esos ~4 s se debe a que el primer intento de asociación al nuevo AP suele fallar y se reintenta tras 3 s. En mediciones de redes 802.11 reales, la fase de escaneo (*probe*) es la que más contribuye a la latencia del traspaso, y esa latencia varía bastante entre un traspaso y otro y según el fabricante [6].

**¿A qué puntos de acceso se conecta?** A ap4, ap0 y ap5. Aunque ap1 y ap7 cubren parte de la ruta, nunca ofrecieron una señal 3 dB mejor que la del AP actual, así que sta3 no se asoció a ellos.

**¿Se conecta al nodo central o pasa directamente de un lóbulo a otro?** Se conecta al nodo central, durante unos 16 s (t ≈ 34–50). La frecuencia de muestreo influye en lo que se observa. Con muestreo cada 3 s, menor que la duración de cada desconexión (~4 s), las dos desconexiones aparecen con seguridad. Con 5 s, que es mayor que la desconexión, verlas depende de la suerte. En esta ejecución coincidieron (t = 31 y t = 51), pero en una ejecución anterior con muestreo de 5 s se perdió una. Las consultas manuales son todavía menos fiables: en la ejecución de 5 s ninguna vio la llegada a ap5 ni una desconexión. Para captar con seguridad un evento, el período de muestreo debe ser menor que la duración del evento.

**¿Qué cambios se detectan en la señal?** La señal sigue el modelo *log-distance* con exponente n = 3,9:

RSSI(d) = P_t + G_t + G_r − PL(1 m) − 10·n·log₁₀(d) = 14 + 5 + 5 − 40 − 39·log₁₀(d) [dBm]

- Al inicio sta3 está a ~16 m de ap4, y se mide −63 dBm. El modelo da 24 − 40 − 39·log₁₀(16) ≈ −63 dBm.
- La ruta pasa a ~3,8 m de ap4, contando el metro de altura. La señal sube a −39 dBm y el modelo da −38,6 dBm.
- Al alejarse de ap4 la señal cae hasta −73/−75 dBm, y entonces ap0 ya la supera en más de 3 dB.
- Con ap0, la señal sube al pasar por el origen (−24 dBm a ~1–2 m) y luego cae hasta −77 dBm.
- Con ap5 sube hasta −19 dBm al llegar sobre el AP, a 1 m de altura.

Cada traspaso ocurre cuando el AP nuevo supera al actual en al menos 3 dB: −76 → −71 dBm y −79 → −75 dBm. Esa histéresis evita que la estación salte repetidamente entre dos AP de señal parecida (efecto *ping-pong*). Eso se observó en una prueba anterior sin histéresis, donde una estación detenida cambió cuatro veces de AP.

**Proceso de desconexión y reconexión suponiendo escaneo activo.** En 802.11 una estación debe asociarse a un AP antes de enviar o recibir datos. Para descubrir los AP disponibles puede usar escaneo pasivo (escuchar los *beacons* que cada AP emite periódicamente) o escaneo activo (enviar *Probe Request* y esperar *Probe Response*) [1, §7.3.1]. Si sta3 usara escaneo activo, el proceso observado sería:

1. **Degradación.** Al alejarse de ap4, la señal cae (−39 → −73 dBm). Esto aumenta la tasa de error y fuerza tasas de transmisión menores. Cuando la señal baja de un umbral, la estación inicia la búsqueda de otro AP.
2. **Escaneo activo.** La estación envía *Probe Request* en cada canal (1 a 11) y los AP que la reciben responden con *Probe Response*, indicando su SSID y la señal con que llegan. En nuestra topología cada AP usa un canal distinto (ap4 en el 2, ap0 en el 1, ap5 en el 5), así que la estación debe recorrer varios canales. Por eso el escaneo suele ser la parte más lenta del traspaso [6].
3. **Selección.** La estación elige el AP con mejor señal, en este caso ap0 cerca del centro y ap5 al final.
4. **Desconexión y (re)asociación.** La estación se desasocia de ap4 (*Disassociation*) y envía *Authentication* y *Reassociation Request* a ap0, que responde con *Reassociation Response*. En los registros esto corresponde al tramo *Not connected* y a la reaparición de "SSID: ap0-ssid". Lo mismo ocurre luego entre ap0 y ap5.
5. **Actualización de la red cableada.** Como los tres AP pertenecen a la misma subred, la estación conserva su IP (10.0.0.3). Los switches/AP del backbone deben aprender que la MAC de sta3 está ahora detrás del nuevo AP. Según [1, §7.3.4], el nuevo AP envía una trama de difusión con la MAC de la estación para actualizar sus tablas.

Mininet-WiFi no emula por defecto el escaneo real. En este script la decisión de traspaso la toma un control que calcula la señal con el mismo modelo de propagación. Por eso el enunciado pide suponer el escaneo activo.

---

## Pregunta 4 – Zonas de cobertura de sta2 y throughput según canales

### 4.1 Zonas de cobertura de sta2

sta2 parte en (−212, 0), fuera de toda cobertura (los AP más cercanos, ap2 y ap3, están a ~105 m y el rango es ~83 m). Recorre el eje X en 40 s hasta (229, 0), también fuera de cobertura. Según el cálculo del script (`--dry-run`), a lo largo de su ruta atraviesa la cobertura de **los ocho AP**, en algunos tramos de hasta cinco a la vez. Según el registro de traspasos, se asoció efectivamente a varios de ellos, así que no fue necesario modificar su ruta:

- Configuración de canales base: ap2 → ap0 → ap6. Los intentos de traspaso a ap4 y ap5 fallaron, y la estación pasó al siguiente AP con mejor señal.
- Configuraciones de la P4: ap3 → ap1 → ap0 → ap5 → ap6.

La diferencia entre ap2 y ap3 al entrar se debe a que ambos están a la misma distancia del eje X (y = ±35). Con distancias iguales, gana el AP de canal más bajo, porque su frecuencia es menor y la pérdida de propagación también.

### 4.2 Cobertura compartida entre sta2 y sta3

Las rutas ya hacen que sta2 y sta3 crucen el origen casi al mismo tiempo, así que la simulación no requirió cambios para que compartieran cobertura. Según el registro de traspasos, **ambas están asociadas a ap0 entre t ≈ 33 y 39 s**. El script se modificó para lanzar automáticamente `iperf` de sta2 a sta3 en t = 34,5 s durante 4 s (opciones `--iperf 34.5 --iperf-dur 4`). También guarda el AP y la señal de ambas estaciones antes y después de la medición. Se hicieron 3 repeticiones por configuración, con wmediumd en modo interferencia. Los canales del nodo central y sus cuatro adyacentes fueron:

| Configuración | ap0 | ap1, ap5 (primer nodo de cada lóbulo) | ap4, ap7 (último nodo de cada lóbulo) |
|---|---|---|---|
| Mismo canal | 6 | 6 | 6 |
| Canales 4, 5 y 6 | 5 | 4 | 6 |
| Canales 1, 6 y 11 | 1 | 6 | 11 |

### 4.3 Resultados

Se reporta el throughput promedio de los primeros 4 s, la ventana en que ambas comparten ap0. El total que entrega iperf incluye la cola de la conexión, que se alarga cuando sta2 cambia de AP al terminar la medición.

| Configuración | Rep. 1 | Rep. 2 | Rep. 3 | Promedio |
|---|---|---|---|---|
| Mismo canal | 15,0 | 14,5 | 15,5 | **15,0 Mbit/s** (desv. 0,5) |
| Canales 4, 5 y 6 | 8,0 \* | 7,1 \* | 15,5 | **10,2 Mbit/s** (desv. 4,6) |
| Canales 1, 6 y 11 | 14,8 | 16,0 | 15,2 | **15,3 Mbit/s** (desv. 0,6) |

\* En estas dos repeticiones sta2 aún no estaba asociada a ap0 al empezar la medición. El primer intento de asociación falló y se completó en t = 36,0–36,7 s, en vez de t ≈ 32,7–33,0 s como en las demás repeticiones. Durante ~2 s de la ventana no hubo enlace. En la única repetición con canales 4, 5 y 6 en que la asociación ocurrió a tiempo, el resultado (15,5 Mbit/s) fue igual al de las otras configuraciones.

En todas las repeticiones el throughput **baja segundo a segundo** (por ejemplo, 18,9 → 18,9 → 13,6 → 12,6 Mbit/s). sta2 se mueve a ~11 m/s y se aleja rápidamente de ap0: su señal pasa de −38 a −83 dBm en esos 4 s, así que baja su tasa de transmisión y aumentan las retransmisiones.

### 4.4 Análisis

**¿Cuál configuración generó mejor rendimiento?** Cuando sta2 alcanzó a asociarse a tiempo, las tres configuraciones dieron prácticamente lo mismo, ~15 Mbit/s. La diferencia entre "mismo canal" (15,0) y "1, 6 y 11" (15,3) es menor que la variación entre repeticiones. El promedio más bajo con canales 4, 5 y 6 se explica por las dos repeticiones en que la asociación se atrasó. Con solo 3 repeticiones no se puede atribuir ese atraso a la configuración de canales.

**¿Por qué ocurre este comportamiento?**

1. **Ambas estaciones están en el mismo AP.** El tráfico sta2 → ap0 → sta3 viaja dos veces por el aire en el canal de ap0, y ese canal se comparte entre las dos transmisiones. El canal de los AP vecinos no cambia esa situación.
2. **No hay tráfico en las celdas vecinas.** Durante la medición, los demás AP solo transmiten *beacons* y las otras estaciones no generan datos. La contención con otras celdas es despreciable, sea cual sea su canal.
3. **El emulador no modela la interferencia entre canales.** En el código de wmediumd, la interferencia que recibe un nodo se suma considerando a todos los transmisores del mismo "medio" (`medium_id`), sin comparar su frecuencia [7]. Por eso no hay diferencia en la interferencia calculada entre canales iguales, solapados (4, 5, 6) o no solapados (1, 6, 11).
4. **La movilidad domina el resultado.** La caída de señal de sta2 durante la medición influye mucho más que la configuración de canales.

**¿Qué debería ocurrir según la teoría?** En 2,4 GHz los canales están separados por 5 MHz, pero cada transmisión ocupa ~20–22 MHz. Por eso solo 1, 6 y 11 no se solapan [1].

- **Mismo canal:** todas las celdas vecinas comparten el medio. Con CSMA/CA las estaciones escuchan antes de transmitir y se turnan (contención y *backoff*), así que el tiempo de aire y el throughput se reparten entre todas [1]. El rendimiento empeora a medida que hay más tráfico en las celdas vecinas.
- **Canales 4, 5 y 6:** son canales parcialmente solapados. La energía del canal vecino llega como ruido que el receptor no puede decodificar. CSMA/CA no coordina con esas transmisiones, así que aumentan los errores y las retransmisiones. En la práctica suele ser igual o peor que usar el mismo canal.
- **Canales 1, 6 y 11:** cada celda vecina usa espectro distinto, sin interferencia ni contención entre celdas. Es la configuración con **mejor rendimiento esperado** y la recomendada para desplegar AP vecinos en 2,4 GHz.

Para observar esa diferencia en el emulador harían falta dos condiciones. La primera, tráfico simultáneo en celdas vecinas, por ejemplo un iperf entre sta1 y sta5 en paralelo. La segunda, un modelo de interferencia que distinga canales, cosa que la versión usada de wmediumd no hace.

---

## Referencias

[1] J. F. Kurose y K. W. Ross, *Computer Networking: A Top-Down Approach*, 8.ª ed. Pearson, 2021, cap. 7 (§7.3.1 arquitectura 802.11, canales y asociación; §7.3.4 movilidad en la misma subred IP). *Verificar que coincida con el capítulo 6 de las clases del curso.*

[2] IEEE Std 802.11-2020, *Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications*.

[3] IEEE Std 802.1D-2004, *Media Access Control (MAC) Bridges* (Spanning Tree Protocol).

[4] A. S. Tanenbaum y D. J. Wetherall, *Computer Networks*, 5.ª ed. Pearson, 2011, §4.8 (puentes y árbol de expansión). *Verificar la sección en la edición disponible.*

[5] R. R. Fontes, S. Afzal, S. H. B. Brito, M. A. S. Santos y C. E. Rothenberg, "Mininet-WiFi: Emulating software-defined wireless networks", *Proc. CNSM*, 2015.

[6] A. Mishra, M. Shin y W. Arbaugh, "An empirical analysis of the IEEE 802.11 MAC layer handoff process", *ACM SIGCOMM Computer Communication Review*, vol. 33, n.º 2, pp. 93–102, 2003.

[7] Código fuente de wmediumd (fork usado por Mininet-WiFi): https://github.com/ramonfontes/wmediumd, archivo `wmediumd/wmediumd.c`, función `get_signal_offset_by_interference`.
