# Guion del video – Laboratorio 5, Grupo 14

**Duración estimada:** 8–9 minutos. Se graba en Ubuntu, con OBS capturando la pantalla completa.

**Cómo leer este guion**

- **[ACCIÓN]** es lo que haces en pantalla. Los comandos salen de `comandos_video.txt`, en el mismo orden.
- **🎙️** es lo que dices. Está escrito para leerse en voz alta y a un ritmo tranquilo. Si te sale más natural con otras palabras, cámbialo, pero mantén los datos.
- **⏳** son tiempos de espera. Ahí conviene hablar mientras la simulación avanza.
- Los números en **〈corchetes angulares〉** se leen de la pantalla, porque pueden variar un poco en cada ejecución.

**Antes de apretar "Grabar"**

```
cd ~/lab5
sudo rm -rf registros
sudo -v
```

Deja abiertos la terminal (con fuente grande), un editor con `lab5_simulacion.py` y otro con `comandos_video.txt`.

---

## Escena 0 – Presentación (≈ 20 s)

🎙️ «Hola. Este es el video del Laboratorio 5 de Redes de Computadores, del grupo 14. Vamos a mostrar la simulación en Mininet-WiFi de una topología de puntos de acceso con forma de lemniscata, la movilidad de las estaciones y las pruebas que pide el enunciado: ping durante el desplazamiento, falla de enlace, seguimiento del punto de acceso de la estación 3 y throughput según la configuración de canales.»

---

## Escena 1 – Topología y código (≈ 1 min 45 s)

**[ACCIÓN]** Ejecuta:

```
python3 lab5_simulacion.py --dry-run
```

🎙️ «Primero, la topología calculada por el script, sin iniciar Mininet. Como somos el grupo 14, N es 6 más 14 módulo 4, o sea, 8 nodos. El exponente de pérdida es 3,5 más 4 décimos: 3,9. Con los valores por defecto de Mininet-WiFi, eso da un rango de cobertura de unos 83 metros por punto de acceso.»

**[ACCIÓN]** Señala con el mouse la lista de puntos de acceso y los enlaces.

🎙️ «El nodo central, ap0, está en el origen. El lóbulo izquierdo tiene cuatro nodos, de ap1 a ap4, y el derecho tres, de ap5 a ap7, en las coordenadas exactas de la tabla del enunciado. Cada lóbulo es un anillo que parte y termina en ap0, así que el nodo central se conecta con cuatro nodos y el resto con sus dos vecinos. Cada punto de acceso usa un canal distinto.»

**[ACCIÓN]** Señala la parte de "Estaciones".

🎙️ «Abajo están las cinco estaciones con sus rutas, y los puntos de acceso que cubren cada tramo. La estación 1 está fija dentro del lóbulo izquierdo. La 2 parte fuera de cobertura y recorre el eje X en 40 segundos. La 3 va en línea recta desde el lóbulo izquierdo hasta ap5, pasando por el centro, en 45 segundos. La 4 parte en el origen y llega al lóbulo derecho en 20 segundos. Y la 5 se mueve en la dirección del eje Y, entrando y saliendo de la zona de solapamiento, durante 70 segundos. Dos decisiones de diseño: las estaciones están a un metro de altura, porque el emulador no admite distancia cero entre nodos, y la estación 5 recorre una recta paralela al eje Y, en x igual a menos 23.»

**[ACCIÓN]** Cambia al editor con `lab5_simulacion.py`. Muestra la creación de los puntos de acceso (`addAccessPoint` con `failMode` y `stp`).

🎙️ «En el código, los puntos de acceso se crean en modo standalone y con Spanning Tree activado. Como los lóbulos son anillos, la red cableada tiene ciclos. STP bloquea un puerto en cada anillo para evitar tormentas de broadcast. Además, dejamos a ap0 como raíz del árbol y acortamos los temporizadores para que converja en pocos segundos.»

**[ACCIÓN]** Baja hasta la clase `ControlTraspaso`.

🎙️ «Esta clase controla la asociación de las estaciones. Cada medio segundo calcula la señal hacia cada punto de acceso con el modelo log-distance. Si la estación sale de cobertura, la desconecta. Si otro punto de acceso supera al actual en al menos 3 dB, hace el traspaso: primero se desconecta y después se asocia al nuevo. Esos 3 dB de histéresis evitan que la estación salte de un lado a otro entre dos puntos de acceso con señal parecida. Cada evento queda registrado en un archivo.»

---

## Escena 2 – Movilidad y ping entre sta2 y sta3 (≈ 1 min 45 s)

**[ACCIÓN]** Vuelve a la terminal y ejecuta:

```
sudo mn -c
sudo python3 lab5_simulacion.py --interferencia --monitor sta3 --cada 1
```

🎙️ «Ahora la simulación completa, con wmediumd en modo interferencia. En este modo, la señal de cada trama depende de la posición de los nodos. También vamos a registrar cada segundo el punto de acceso de la estación 3.»

**[ACCIÓN]** Cuando aparezca el plano, acomoda la ventana para que se vean el plano y la terminal.

🎙️ «Este es el plano: los puntos de acceso con su círculo de cobertura y las cinco estaciones. Las estaciones empiezan a moverse a los 15 segundos, para que antes converja Spanning Tree.»

**[ACCIÓN]** En la CLI, apenas aparezca `mininet-wifi>`:

```
sta2 ping -D -i 0.2 sta3
```

🎙️ «Hacemos ping continuo de la estación 2 a la 3, cada 0,2 segundos. Al principio el destino es inalcanzable, porque la estación 2 todavía está fuera de cobertura.»

⏳ **[ACCIÓN]** Deja correr el ping unos 50 s mirando el plano. Narra cuando ocurra cada cosa:

🎙️ (cuando empiecen las respuestas) «Ahora la estación 2 entró a la cobertura del lóbulo izquierdo y el ping responde, con un RTT de alrededor de un milisegundo. Las primeras respuestas llegan juntas y con tiempos altos que van bajando: son los paquetes que quedaron en cola mientras se resolvía ARP.»

🎙️ (cuando aparezcan pérdidas cerca del centro) «Aquí se pierden paquetes. Las dos estaciones cruzan el centro y cambian de punto de acceso casi al mismo tiempo. Cada traspaso es del tipo break-before-make: la estación se desconecta antes de asociarse al nuevo punto de acceso, así que durante unos segundos no tiene enlace.»

🎙️ (al final, con sta2 lejos a la derecha) «Y aquí la estación 2 sale de la cobertura del lóbulo derecho, así que la comunicación se pierde hasta el final.»

**[ACCIÓN]** Ctrl + C.

🎙️ «En resumen: 〈leer "packets transmitted" y "% packet loss"〉. Las pérdidas se concentran fuera de cobertura y en los traspasos.»

---

## Escena 3 – Punto de acceso de sta3 (≈ 1 min 15 s)

**[ACCIÓN]** En la misma CLI:

```
sta3 iw dev sta3-wlan0 link
```

🎙️ «Con iw vemos a qué punto de acceso está conectada la estación 3, con qué SSID y con qué señal. Ahora está en 〈leer SSID〉, con 〈leer signal〉 dBm.»

**[ACCIÓN]**

```
sh grep -E "== t=|SSID|signal|Not connected" registros/sta3_cada1*.log | tail -n 60
```

🎙️ «Este es el registro tomado cada segundo durante todo el recorrido. La estación 3 parte en ap4, con una señal que sube a unos menos 39 dBm cuando pasa cerca, y luego baja a medida que se aleja. Después hay unos segundos sin conexión, que corresponden al traspaso. Luego queda en ap0, el nodo central, y finalmente en ap5. O sea, sí se conecta al nodo central: no salta directo de un lóbulo al otro. En el informe comparamos este registro con muestreos cada 3 y cada 5 segundos. Con 5 segundos se pueden perder las desconexiones, porque duran unos 4 segundos.»

**[ACCIÓN]**

```
sh cat registros/traspasos_*.log
```

🎙️ «En el registro de traspasos se ve por qué cambió: pasó de ap4 a ap0 cuando ap0 lo superó en más de 3 dB, de 〈leer, aprox. −76〉 a 〈leer, aprox. −71〉 dBm. Lo mismo ocurrió entre ap0 y ap5.»

**[ACCIÓN]** `exit`

---

## Escena 4 – Falla de enlace y nodo central (≈ 2 min)

**[ACCIÓN]**

```
sudo mn -c
sudo python3 lab5_simulacion.py --interferencia
```

🎙️ «Ahora probamos qué pasa si falla un enlace del nodo central. La estación 1 está asociada a ap4, así que el enlace relevante para nuestro caso es ap0–ap4, el equivalente al ap0–ap1 del enunciado. Esperamos a que las estaciones 1 y 4 estén quietas.»

⏳ **[ACCIÓN]** Espera ~35 s desde que aparece la CLI. Mientras tanto:

🎙️ «Mientras esperamos: con Spanning Tree, el árbol tiene su raíz en ap0, y en cada anillo hay un puerto bloqueado que corta el ciclo. Si un enlace activo falla, ese puerto bloqueado tiene que pasar a reenviar tráfico. Pero el protocolo no lo hace de inmediato, para no formar ciclos transitorios.»

**[ACCIÓN]**

```
sh ovs-appctl stp/show ap3
```

🎙️ «En ap3, el puerto eth2, hacia ap2, está en estado blocking: ese es el puerto que corta el ciclo del anillo izquierdo.»

**[ACCIÓN]**

```
sta1 ping -D -i 0.2 sta4 > registros/ping_falla.txt &
link ap0 ap4 down
```

🎙️ «Dejamos un ping en segundo plano de la estación 1 a la 4 y bajamos el enlace entre ap0 y ap4.»

⏳ **[ACCIÓN]** Espera ~20 s.

🎙️ «Durante estos segundos no hay comunicación. Spanning Tree debe esperar el tiempo max-age, de 6 segundos, y luego pasar el puerto por los estados listening y learning, de 4 segundos cada uno. Eso suma unos 14 segundos.»

**[ACCIÓN]**

```
sh ovs-appctl stp/show ap3
sh ovs-appctl stp/show ap4
```

🎙️ «Ahora el puerto de ap3 que estaba bloqueado es puerto raíz y está reenviando tráfico, y ap4 llega a la raíz a través de ap3, con costo 8 en vez de 2. El tráfico ahora recorre el anillo izquierdo en sentido contrario: ap4, ap3, ap2, ap1 y ap0.»

**[ACCIÓN]**

```
sh pkill -INT ping
sh tail -n 5 registros/ping_falla.txt
```

🎙️ «El resumen del ping muestra 〈leer % packet loss〉 de pérdida. Toda corresponde a la interrupción de unos 13 segundos mientras Spanning Tree se reconfiguraba. Después la comunicación se mantiene.»

**[ACCIÓN]**

```
link ap0 ap1 down
link ap0 ap5 down
link ap0 ap7 down
sta1 ping -c 5 sta4
```

🎙️ «Por último, si el nodo central deja de funcionar, lo que simulamos bajando sus cuatro enlaces, el ping falla al cien por ciento. ap0 es el único nodo que une los dos lóbulos: es un punto único de falla. Cada lóbulo sigue conectado por dentro, pero no existe ningún camino entre ellos que Spanning Tree pueda activar. Para evitarlo, habría que agregar un enlace directo entre los lóbulos o un segundo nodo central.»

**[ACCIÓN]** `exit`

---

## Escena 5 – Throughput según canales (≈ 1 min)

**[ACCIÓN]**

```
sudo mn -c
sudo python3 lab5_simulacion.py --interferencia --canales 1611 --iperf 34.5 --duracion 45 --sin-grafico
```

🎙️ «Para la pregunta 4 medimos el throughput entre las estaciones 2 y 3 mientras ambas están asociadas a ap0. Según el registro de traspasos, eso ocurre entre los segundos 33 y 39. El script lanza iperf automáticamente en el segundo 34,5 durante 4 segundos. Esta ejecución usa los canales 1, 6 y 11 en el nodo central y sus adyacentes.»

⏳ (la ejecución dura ~45 s)

🎙️ «Repetimos esta medición tres veces con cada configuración: todos en el mismo canal, canales 4, 5 y 6, y canales 1, 6 y 11.»

**[ACCIÓN]**

```
cat registros/iperf_1611_*.txt
```

🎙️ «Antes de medir, las dos estaciones estaban en ap0. El throughput fue de 〈leer los primeros intervalos〉 megabits por segundo, y va bajando cada segundo porque la estación 2 se aleja rápido de ap0.»

**[ACCIÓN]** Muestra la tabla de la Pregunta 4 del informe (o del borrador).

🎙️ «Con las tres configuraciones obtuvimos alrededor de 15 megabits por segundo cuando la asociación ocurrió a tiempo. La teoría dice que 1, 6 y 11 debería rendir mejor, porque son los únicos canales de 2,4 GHz que no se solapan, y que los canales solapados deberían rendir peor. En el emulador no se nota por tres razones: las dos estaciones están en el mismo punto de acceso, no hay tráfico en las celdas vecinas, y wmediumd no distingue canales al calcular la interferencia.»

---

## Cierre (≈ 15 s)

🎙️ «Eso es todo. El código, el README con las instrucciones y el informe con el análisis completo de cada pregunta están en la entrega. Gracias.»

**[ACCIÓN]** Detén la grabación.
