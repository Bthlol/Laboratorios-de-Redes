# Resumen de resultados – Laboratorio 5, Grupo 14

Todas las mediciones se hicieron el 23/11 en Ubuntu 26.04 nativo con Mininet-WiFi y wmediumd en modo interferencia (`--interferencia`). Los tiempos (t) se miden desde el inicio de la red; las estaciones empiezan a moverse cerca de t ≈ 16 s. El análisis completo de cada pregunta está en el informe.

## P2 – Ping entre pares y falla de enlace

**Par A, sta1 → sta4** (`datos/p2/ping_sta1_sta4.txt`, `traspasos_190012.log`, `sta4_cada1.0s_190012.log`)

- 397 enviados, 375 recibidos, **5,5 % de pérdida**, RTT promedio 1,7 ms.
- Pérdidas al inicio, antes de resolver ARP (t ≈ 11–14,5 s).
- Solo 2 paquetes perdidos (~0,6 s) en el traspaso de sta4 ap0 → ap5 (t = 30,4 s).
- Picos de RTT de 6–63 ms mientras sta4 se aleja de ap0.

**Par B, sta2 → sta3** (`datos/p2/ping_sta2_sta3.txt`, `traspasos_190308.log`, registros de sta2 y sta3)

- 290 enviados, 95 recibidos, **67 % de pérdida**.
- sta2 está fuera de cobertura al inicio y al final.
- Corte de ~6,5 s cuando ambas cambian de AP casi a la vez (t ≈ 28–35 s), y de ~4,2 s en el traspaso de sta2 ap0 → ap6.
- Al reconectar, la cola de ARP hace que el RTT baje de 1013 a 184 ms.

**Falla del enlace ap0–ap4** (`datos/p2/falla_enlace_ap0_ap4_y_nodo_central.txt`)

- Antes del corte, `ap3-eth2` (enlace ap2–ap3) está en *blocking*.
- Tras `link ap0 ap4 down`: **61 paquetes perdidos, ~12,9 s sin servicio**. Coincide con max-age + 2 × forward-delay = 6 + 8 = 14 s.
- Camino nuevo: sta1 → ap4 → ap3 → ap2 → ap1 → ap0 → ap5 → sta4. El costo de ap4 a la raíz pasa de 2 a 8.
- Con los 4 enlaces de ap0 caídos: **100 % de pérdida**. ap0 es un punto único de falla.
- *Esta prueba se hizo con una versión anterior del script (antes de la altura de 1 m y del control de traspaso propio). El resultado depende solo de STP en la red cableada, con estaciones quietas.*

## P3 – AP de sta3

(`datos/p3/`: registros cada 5 s, cada 3 s y cada 1 s, traspasos y consultas manuales)

- Secuencia: **ap4 → ap0 → ap5**, igual en las 4 ejecuciones. sta3 **sí pasa por el nodo central**, unos 16 s.
- Traspasos: ap4 (−76 dBm) → ap0 (−71 dBm) en t ≈ 29,8 s, y ap0 (−79) → ap5 (−75) en t ≈ 50,3 s. En ambos casos el AP nuevo supera al actual en ≥ 3 dB.
- Dos desconexiones de ~4 s cada una (en el registro de 1 s: t = 30–33 y 51–54).
- Con muestreo cada 3 s se ven siempre; con 5 s, depende de la suerte. Las consultas manuales de la ejecución de 5 s nunca vieron una desconexión.
- La señal coincide con el modelo: −63 dBm a 16 m y −39 dBm a 3,8 m. Fórmula: 24 − 40 − 39·log₁₀(d).

## P4 – Throughput sta2 → sta3 según canales

(`datos/p4/iperf_*.txt`; ambas estaciones en ap0 entre t ≈ 33 y 39 s; iperf desde t = 34,5 s durante 4 s)

| Canales (ap0 y sus 4 adyacentes) | Rep. 1 | Rep. 2 | Rep. 3 | Promedio (0–4 s) |
|---|---|---|---|---|
| Todos en el mismo canal (6) | 15,0 | 14,5 | 15,5 | **15,0 Mbit/s** |
| 4, 5 y 6 | 8,0 \* | 7,1 \* | 15,5 | **10,2 Mbit/s** |
| 1, 6 y 11 | 14,8 | 16,0 | 15,2 | **15,3 Mbit/s** |

\* En esas dos repeticiones sta2 aún no estaba asociada a ap0 al iniciar iperf (la asociación se atrasó ~3 s).

- Con asociación a tiempo, las tres configuraciones dan ~15 Mbit/s.
- El emulador no reproduce la diferencia teórica a favor de 1, 6 y 11, por tres razones: ambas estaciones están en el mismo AP, no hay tráfico en las celdas vecinas, y wmediumd calcula la interferencia por "medio" sin distinguir canales.
- El throughput baja cada segundo (≈ 19 → 12,6 Mbit/s), porque sta2 se aleja de ap0 a ~11 m/s.

## Prueba en la VM del curso

`datos/prueba_vm/resumen_prueba_vm.png`: el script corre en el OVA oficial (Lubuntu 20.04) sin avisos ni errores. Los traspasos ocurren en los mismos instantes (±1 s) que en Ubuntu nativo.
