# Plan de trabajo — Laboratorio 3 de Redes de Computadores (Grupo 14)

Integrantes: Sebastián, Benjamín y Bárbara. Entrega: **30 de octubre de 2026, 23:59**, por Aula, como `L3-Grupo14.zip`. Cada hora de atraso descuenta 18 puntos, así que conviene subirlo el 29.

La idea central: cada integrante configura 4 de los 12 routers y responde 2 de las 6 preguntas. Como todas las direcciones están fijadas de antemano en el contrato (sección 2), nadie depende del trabajo de otro para avanzar.

---

## 1. Reparto de trabajo

| Integrante | Routers | Qué configura | Preguntas | Rol transversal |
| --- | --- | --- | --- | --- |
| Sebastián | Deadlock, Cypher, Raze, Killjoy (AS 10) | 4 LAN (9 equipos), OSPF área 0, redistribución y eBGP hacia AS 20 | Q3, Q5 | Integrador del `.pkt` final |
| Benjamín | Neon, Fade (AS 20), Gekko, Viper (AS 30) | LAN de Gekko y Viper (6 equipos), DHCP, BGP | Q1, Q4 | Control formal: nombres, roles USM, contenido del zip |
| Bárbara | Reyna, Omen, Sage (AS 40), Brimstone (AS 50) | LAN de Reyna, Omen y Brimstone (7 equipos), BGP | Q2, Q6 | Maquetación del PDF |

Cada integrante entrega tres cosas:

1. Un archivo `configs/<Router>.txt` por router, con los comandos IOS (sirve para pegarlos en el `.pkt` final y para el Registro de configuración).
2. Las capturas de su zona en `evidencias/Q<n>_*/`.
3. Su parte del informe (sección 6).

### Tareas por persona

**Sebastián**

- [ ] Configurar Deadlock, Cypher, Raze y Killjoy: interfaces de enlace, interfaz LAN (primera IP útil) y equipos con IP estática desde `.2`.
- [ ] OSPF proceso 1, área 0, publicando las LAN y los enlaces 1.0.0.0 a 4.0.0.0. **No** publicar 5.0.0.0 ni 6.0.0.0.
- [ ] eBGP del AS 10 en Raze (vecino 5.0.0.2, AS 20) y Killjoy (vecino 6.0.0.2, AS 20), con redistribución mutua: `redistribute ospf 1` dentro de BGP y `redistribute bgp 10 subnets` dentro de OSPF.
- [ ] Comprobar `show ip ospf neighbor` y pings entre las 4 LAN del AS 10.
- [ ] Armar el `.pkt` maestro pegando los `.txt` de los tres, y avisar cuando esté listo para pruebas entre zonas.
- [ ] Q3 (ruta de Turret a Location server, OSPF vs BGP) y Q5 (efecto de `bandwidth 150` en el enlace 2.0.0.0).
- [ ] Entregar a Bárbara la captura de `show ip route` en Killjoy para la Q6.
- [ ] Memoria de cálculo de las 4 LAN de Base Alfa, registro de sus routers y su párrafo de conclusiones (OSPF y redistribución).

**Benjamín**

- [ ] Configurar Neon, Fade, Gekko y Viper: interfaces de enlace, interfaz LAN en Gekko y Viper.
- [ ] DHCP en Gekko y Viper: excluir las primeras 10 IP útiles, pool `POOL_LAN`, `network`, `default-router` (la IP del router) y `dns-server 0.0.0.0`. Dejar los hosts en modo DHCP y comprobar IP, máscara y puerta de enlace.
- [ ] BGP: AS 20 en Neon y Fade, AS 30 en Gekko y Viper, con los vecinos de la tabla de enlaces. Cada `network` debe llevar la máscara exacta que aparece en la tabla de rutas.
- [ ] Q1 (proceso DORA en modo Simulación entre Wingman y Gekko, y qué pasa en un segmento sin pool) y Q4 (caída del enlace 5.0.0.0 y reconvergencia entre las LAN de Raze y Reyna).
- [ ] Memoria de cálculo de las LAN de Gekko y Viper, registro de sus routers y su párrafo de conclusiones (DHCP, BGP y reconvergencia).
- [ ] Portada con nombres y roles USM correctos de los tres, y revisión formal final del zip.

**Bárbara**

- [ ] Configurar Reyna, Omen, Sage y Brimstone: interfaces de enlace, interfaz LAN (Reyna, Omen) y la LAN 192.168.50.0/24 de Brimstone con Location server.
- [ ] BGP: AS 40 en Reyna, Omen y Sage; AS 50 en Brimstone. Brimstone debe publicar 192.168.50.0/24 y el enlace 13.0.0.0.
- [ ] Resolver el iBGP dentro del AS 40 (ver sección 4, punto 6): hay una propuesta comentada en `Reyna.txt`, `Omen.txt` y `Sage.txt`. Si funciona, se activa; si no, se consulta.
- [ ] Q2 (pings y traceroute de GravNet a Location server y de Spycam a Shrouded Step, con cada router intermedio) y Q6 (`show ip route` de Killjoy y Sage, identificación de rutas O, O E2 y B, y distancia administrativa).
- [ ] Memoria de cálculo de las LAN de Reyna, Omen y Brimstone, registro de sus routers y su párrafo de conclusiones (BGP en el AS 40 y tablas de rutas).
- [ ] Ensamblar y maquetar el PDF final.

---

## 2. Contrato compartido de direccionamiento

Si los tres respetan estas tablas, cualquiera configura su router sin saber qué hizo el otro. La versión autoritativa se genera con `scripts/generar.py` (ver `contrato/plan_ip.md`); estas tablas son su resumen.

### 2.1 Enlaces entre routers

Todos usan máscara 255.0.0.0 (/8). El router nombrado primero en el enunciado toma `.1` y el segundo `.2`.

| Red | Router .1 | Router .2 | Sesión o protocolo |
| --- | --- | --- | --- |
| 1.0.0.0/8 | Deadlock | Cypher | OSPF |
| 2.0.0.0/8 | Deadlock | Raze | OSPF |
| 3.0.0.0/8 | Cypher | Killjoy | OSPF |
| 4.0.0.0/8 | Raze | Killjoy | OSPF |
| 5.0.0.0/8 | Raze | Neon | eBGP AS 10 ↔ AS 20 |
| 6.0.0.0/8 | Killjoy | Fade | eBGP AS 10 ↔ AS 20 |
| 7.0.0.0/8 | Fade | Viper | eBGP AS 20 ↔ AS 30 |
| 8.0.0.0/8 | Neon | Gekko | eBGP AS 20 ↔ AS 30 |
| 9.0.0.0/8 | Viper | Omen | eBGP AS 30 ↔ AS 40 |
| 10.0.0.0/8 | Omen | Sage | AS 40 (interno) |
| 11.0.0.0/8 | Reyna | Sage | AS 40 (interno) |
| 12.0.0.0/8 | Gekko | Reyna | eBGP AS 30 ↔ AS 40 |
| 13.0.0.0/8 | Sage | Brimstone | eBGP AS 40 ↔ AS 50 |

### 2.2 Subredes LAN

Variables: **Y = 14** (número de grupo) y **X = 4** (último dígito). El router toma siempre la primera IP útil de su subred y los equipos van desde `.2` en el orden del enunciado.

Hay dos formas de contar las subredes (ver sección 4, punto 1), por eso hay dos columnas de resultado. Por defecto el repositorio usa el criterio 2.

| LAN | Base y regla | Máscara | Criterio 1: la subred cero cuenta como 1.ª | Criterio 2: se excluye la subred cero |
| --- | --- | --- | --- | --- |
| Deadlock | 172.16.0.0/16 en 32 subredes (5 bits), la 3.ª | /21 = 255.255.248.0 | 172.16.16.0 | 172.16.24.0 |
| Raze | igual, la 8.ª | /21 | 172.16.56.0 | 172.16.64.0 |
| Killjoy | igual, la 15.ª | /21 | 172.16.112.0 | 172.16.120.0 |
| Cypher | igual, la 24.ª | /21 | 172.16.184.0 | 172.16.192.0 |
| Gekko | 20.25.0.0/16 con (4/2)+2 = 4 bits, la primera | /20 = 255.255.240.0 | 20.25.0.0 | 20.25.16.0 |
| Viper | 48.7.0.0/16 con 14+25 = 39 hosts (6 bits de host), la primera | /26 = 255.255.255.192 | 48.7.0.0 | 48.7.0.64 |
| Reyna | 183.0.0.0/8 en 2×(4+8) = 24 o más subredes (5 bits = 32), la 14.ª | /13 = 255.248.0.0 | 183.104.0.0 | 183.112.0.0 |
| Omen | 4.93.0.0/16 en 32 subredes, la 14.ª | /21 | 4.93.104.0 | 4.93.112.0 |
| Brimstone | 192.168.50.0/24 (dada) | /24 | 192.168.50.0 | 192.168.50.0 |

### 2.3 Equipos por LAN

| LAN | Equipos | Asignación |
| --- | --- | --- |
| Deadlock | GravNet, Annihilation | estática |
| Raze | Paint Shells, Pack Blast | estática |
| Killjoy | Turret, Lockdown | estática |
| Cypher | Trapwire, Spycam, Base server | estática |
| Gekko | Wingman, Dizzy, Thrash | DHCP |
| Viper | Poison Cloud, Snake Bite, Viper's Pit | DHCP |
| Reyna | Dismiss, Devour, Empress | estática |
| Omen | Paranoia, Dark cover, Shrouded Step | estática |
| Brimstone | Location server | estática |

---

## 3. Reglas para que nadie bloquee a nadie

- **Misma base, zonas separadas.** Todos parten de la topología entregada, trabajan en su copia (por ejemplo `borrador_Benjamin.pkt`) y solo tocan sus 4 routers.
- **Un `.txt` por router.** Cada router queda guardado como `configs/<Router>.txt` con interfaces, DHCP, OSPF, BGP y redistribución. Con eso se arma el `.pkt` final y también el Registro de configuración del informe.
- **Integrar pegando, no fusionando.** El `.pkt` maestro se arma pegando esos `.txt` en la topología original, así no hay que mezclar archivos `.pkt` de tres personas.
- **Qué se puede probar solo.** Pings de cada host a su puerta de enlace, DHCP (Gekko y Viper) y OSPF completo (los 4 routers del AS 10 son de Sebastián). Las sesiones BGP solo llegan a *Established* cuando ambos extremos están configurados, así que se verifican en la integración.
- **Si alguien se ausenta.** Si pasan 24 horas sin noticias del plazo de una fase, los otros dos se reparten sus routers (2 cada uno) y los configuran desde el contrato; no hace falta nada del ausente.
- **Cambios al contrato.** Cualquier cambio de IP o de criterio se avisa en el chat del grupo antes de aplicarse. Cada noche cada uno deja una línea: hecho, en curso o bloqueado.
- **Capturas.** Se nombran `Q<n>_<descripcion>.png` y se guardan en `evidencias/` desde el primer día.
- **Originalidad.** Ningún `.pkt` sale del grupo: el enunciado califica con nota 0 cualquier sospecha de copia o intercambio entre grupos.

---

## 4. Dudas del enunciado para consultar a los ayudantes

Cristóbal Brandau y Juan Cucurella. Estas cinco cosas cambian lo que se configura o cómo se nombran los archivos; conviene escribirles antes de dar nada por definitivo.

1. **Cómo contar las subredes.** "3.ª subred útil" y "primera subred válida" sugieren el criterio clásico (se excluye la subred cero, criterio 2), pero "32 subredes distintas" para Omen sugiere usar las 32. Hasta tener respuesta, el grupo adopta un solo criterio y lo declara en la memoria de cálculo.
2. **Quién hace la redistribución.** La sección 3.6.3 del enunciado nombra a Neon y Fade con `router bgp 10`, pero ambos son del AS 20; los que corren OSPF y están en el AS 10 son Raze y Killjoy, y la pregunta 6 trata a Killjoy como router de frontera. La lectura más coherente es redistribuir en Raze y Killjoy, con eBGP hacia Neon y Fade. Los `.txt` del repositorio ya están así.
3. **Direcciones que se pisan.** La LAN de Omen (4.93.x.x) cae dentro de la red 4.0.0.0/8 del enlace Raze–Killjoy. Funciona por prefijo más largo, pero hay que explicarlo si aparece en una tabla de rutas.
4. **Enlaces dentro de un mismo AS.** Según el enunciado no hay enlace directo Neon–Fade ni Gekko–Viper, así que cada uno se une al resto solo por eBGP. Hay que confirmarlo abriendo la topología entregada en Packet Tracer, junto con los nombres de interfaz de cada router (se anotan en `contrato/interfaces.json`).
5. **Nombre exacto de los archivos de entrega.** El texto del enunciado muestra "Informe L3 Grupo[Nº].pdf" y "Topologia L3 Grupo[Nº].pkt", probablemente con guiones bajos que se perdieron al convertir el PDF. Confirmarlo en el original: un error cuesta 15 puntos.
6. **iBGP dentro del AS 40** (punto técnico para Bárbara). Reyna, Omen y Sage probablemente necesitan iBGP entre sí (con `next-hop-self`) para pasar rutas de un lado a otro; el enunciado no lo pide explícitamente. Hay una propuesta con Sage como *route-reflector*, comentada en los `.txt`, que no está probada en Packet Tracer.

---

## 5. Cómo trabajar con el repositorio

El `README.md` resume la estructura de carpetas y los comandos.

- Repositorio **privado**. Los `.pkt` no se versionan (`.gitignore`); van en una carpeta compartida aparte y solo Sebastián toca el maestro.
- Cada uno edita solo sus archivos (routers, preguntas y conclusión), así no hay conflictos al mezclar. Hacer `git pull --rebase` antes de empezar.
- **Completar interfaces:** abrir la topología en Packet Tracer y llenar cada `COMPLETAR` de `contrato/interfaces.json` con el nombre real de la interfaz. Conviene que cada uno llene solo sus routers.
- **Generar:** `python3 scripts/generar.py` (o `--criterio 1`) regenera `configs/`, `contrato/plan_ip.md` y las tablas del informe. Si alguien edita `generar.py`, avisa en el chat: afecta a los tres.
- **Informe:** se compila desde `main.tex` (pdfLaTeX, también en Overleaf). Cada `\pend{...}` se reemplaza por texto; antes de entregar no debe quedar ningún "PENDIENTE" en el PDF.
- Overleaf no ejecuta Python: las tablas y configuraciones se generan fuera y se suben ya listas.

---

## 6. Informe: quién escribe qué

| Sección del informe | Escribe | Contenido |
| --- | --- | --- |
| 1. Portada | Benjamín | Nombres y roles USM de los tres (un error cuesta 5 puntos) |
| 2. Memoria de cálculo | Cada uno, sus LAN | Red, máscara decimal y CIDR, rango útil, broadcast y dispositivo; sustitución explícita de X = 4 e Y = 14. Sebastián: 4 LAN de Base Alfa. Benjamín: Gekko y Viper. Bárbara: Reyna, Omen y Brimstone |
| 3. Registro de configuración | Cada uno, sus routers | Los `.txt` de cada router ordenados por bloque (interfaces, DHCP, OSPF, BGP, redistribución) |
| 4. Preguntas y análisis | Sebastián: Q3, Q5. Benjamín: Q1, Q4. Bárbara: Q2, Q6 | Respuesta analítica con capturas de Packet Tracer y salidas de `show ip route`, `show ip ospf neighbor` y `show ip bgp`. Para Q6, Sebastián aporta la salida de Killjoy y Bárbara la de Sage |
| 5. Conclusiones técnicas | Cada uno, un párrafo | Sebastián sobre OSPF, Benjamín sobre DHCP y BGP, Bárbara sobre redistribución y tablas de rutas; todos incluyen dificultades y lecciones |

---

## 7. Entrega

El paquete final es `L3-Grupo14.zip` (solo `.zip`; `.rar`, `.7z` o `.tar.gz` cuentan como entrega no realizada), con **exactamente dos archivos** dentro: el informe en PDF y el `.pkt` con la topología completamente configurada.

`scripts/empaquetar.py` lo arma desde la carpeta `entrega/`. Lista de control antes de subirlo:

- [ ] El zip se llama `L3-Grupo14.zip` y los dos archivos internos llevan el número 14 con el formato exacto del enunciado (error de nombre: −15 puntos).
- [ ] Contiene solo el PDF del informe y el `.pkt`, nada más.
- [ ] Los roles USM de los tres están correctos en la portada (error: −5 puntos).
- [ ] El `.pkt` abre, las tablas de rutas están completas y los pings de la Q2 funcionan.
- [ ] Se revisó la ortografía y redacción del PDF completo (faltas graves: hasta −5 puntos).
- [ ] No queda ningún `\pend` ni recuadro rojo de captura faltante.
- [ ] Un solo integrante lo sube a Aula antes de las 23:59 del 30 de octubre, idealmente el 29.
