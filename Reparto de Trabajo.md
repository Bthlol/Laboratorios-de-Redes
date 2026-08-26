# Reparto de trabajo — Laboratorio 1 (Redes de Computadores) — Grupo 14

Este documento explica **por qué** dividimos el trabajo de esta forma y **qué le corresponde a cada uno**, para que todos partamos con el mismo criterio antes de escribir código.

## 1. Contexto: dos codebases, no un solo programa

El enunciado nos obliga a separar el sistema en dos lados que corren en **lenguajes distintos** y solo se comunican por protocolo de red (nunca comparten código):

- **Servidor → Go 1.20+** (nos toca por ser grupo par).
- **Cliente → Python 3.10+**.

Esto ya nos da una primera división natural: **nadie que trabaje en el cliente va a tocar jamás un archivo `.go`, y viceversa**. Cero conflictos de merge entre esos dos mundos.

Dentro del servidor, sin embargo, hay algo importante: el **Componente 2 (TCP)** y el **Componente 3 (UDP)** *comparten estado en memoria* — el mapa de sesiones activas, los sockets conectados y los timestamps de heartbeat. Si dos personas distintas tocan ese mapa compartido al mismo tiempo, vamos a tener bugs de concurrencia difíciles de debuggear (condiciones de carrera, sesiones que se cierran solas, etc.) y muchísima fricción de coordinación. **Por eso TCP y UDP van con la misma persona.**

En cambio, el **Componente 1 (HTTP + CSV)** es el más independiente de todos: solo necesita `usuarios.csv` y `historial.csv`, no toca el mapa de sesiones en memoria para nada. Puede desarrollarse y probarse en paralelo sin pisarle el código a nadie.

Otra ventaja clave: **el protocolo (formatos de comandos, códigos de respuesta, estructura de los CSV) ya viene 100% definido en el enunciado.** Eso significa que no necesitamos reunirnos constantemente mientras programamos — cada uno puede construir su parte contra ese "contrato" fijo y recién integrar al final.

## 2. Resumen del reparto

| Persona | Lenguaje | Componentes | Carpeta |
| --- | --- | --- | --- |
| **Benja** | Go | 1. Servicio HTTP de registro + utilidades CSV compartidas | `server-go/internal/storage/`, `server-go/internal/httpserver/` |
| **Seba** | Go | 2. TCP (auth/mensajería/broadcast) + 3. UDP (heartbeat/watchdog) | `server-go/internal/session/`, `server-go/internal/tcpserver/`, `server-go/internal/udpserver/` |
| **Barbie** | Python | 4. Cliente integrado (HTTP + TCP + UDP) | `client-py/` |

## 3. Detalle por persona

### Benja — Servidor HTTP + persistencia (Go)

**Por qué esta parte:** es la más aislada del resto — no depende del estado de sesiones activas, solo de archivos en disco. Ideal para empezar sin esperar a nadie.

**Debe entregar:**
1. `internal/storage/csv.go`:
   - `UsuariosStore`: `UserExists`, `ValidateCredentials`, `RegisterUser` (esta última la usará también Seba en el LOGIN, así que debe quedar lista temprano y con una firma clara).
   - `HistorialStore`: `AppendMensaje`, `LeerHistorialComoTexto` (esta última la usa Seba al guardar cada MSG).
2. `internal/httpserver/http.go`:
   - `POST /register`: valida `username`/`password`, responde `201 Created`, `409 Conflict` o `400 Bad Request` según corresponda.
   - `GET /history`: devuelve el contenido de `historial.csv`.
3. Estructura exacta en `usuarios.csv`: `username,password,fecha_registro`.

**Punto de contacto con Seba:** las funciones `ValidateCredentials` y `AppendMensaje` del storage. Definan juntos la firma de esas funciones **antes** de programar, así Seba puede avanzar el LOGIN/MSG sin esperar la implementación completa de Benja (solo necesita la firma).

### Seba — Núcleo TCP + UDP (Go)

**Por qué esta parte:** concentra todo el estado compartido en memoria (sesiones activas, sockets, heartbeats). Mantenerlo en una sola persona evita que dos personas se pisen escribiendo/leyendo la misma estructura de datos concurrente.

**Debe entregar:**
1. `internal/session/session.go`: el `Manager` de sesiones —`Crear`, `Validar`, `TocarHeartbeat`, `Expirar`, `Broadcast`— protegido con mutex. Aquí vive el mapa `token -> Sesión`.
2. `internal/tcpserver/tcp.go`:
   - `LOGIN <user> <pass>` → valida contra el storage de Benja, genera token único (TTL 10 min), responde `OK <token> <puerto_udp>` o `ERROR INVALID CREDENTIALS`.
   - `MSG <token> <mensaje>` → valida sesión, guarda en historial (vía storage de Benja), responde `ACK`, hace broadcast `INCOMING <user> <mensaje>` al resto de clientes conectados.
   - Estructura exacta en `sesiones.csv`: `token,username,timestamp_creacion,timestamp_ultimo_heartbeat,estado`.
3. `internal/udpserver/udp.go`:
   - Recibe `HEARTBEAT <token>` y actualiza el último heartbeat.
   - Watchdog en segundo plano: expira sesiones sin primer latido en 30s, sin heartbeat en 60s, o al cumplir 10 min de TTL absoluto.

**Punto de contacto con Benja:** consumir `ValidateCredentials` y `AppendMensaje` sin reimplementar acceso a archivos por su cuenta (nunca abrir los CSV directamente desde `tcpserver`/`udpserver`).

### Barbie — Cliente integrado (Python)

**Por qué esta parte:** al estar en un lenguaje distinto, es un módulo completamente autocontenido — su trabajo es "hablar" el protocolo que Benja y Seba están construyendo, sin poder tocar (ni romper) su código.

**Debe entregar:**
1. `http_client.py`: petición `POST /register` armada **a mano** sobre un socket TCP crudo (prohibido usar `urllib.request`/`requests`).
2. `tcp_client.py`: `LOGIN`, envío de `MSG`, y un **hilo receptor** que escucha continuamente el socket y muestra los `INCOMING` sin bloquear la consola.
3. `udp_client.py`: hilo que envía `HEARTBEAT <token>` cada 3 segundos, sin interrupciones, mientras la sesión esté activa.
4. `main.py`: orquesta todo — registro, login, arranque de ambos hilos, y el loop de consola donde el usuario escribe mensajes sin que eso bloquee la recepción de mensajes entrantes.

**Punto de contacto con Benja y Seba:** el contrato de protocolo tal cual está en el enunciado (formatos `LOGIN/OK/ERROR/MSG/ACK/INCOMING/HEARTBEAT`). Barbie puede desarrollar y probar su parte contra un servidor Go a medio implementar, siempre que Benja y Seba respeten esos formatos exactos.

## 4. Orden de trabajo sugerido

1. **Día 1–2:** Benja y Seba se ponen de acuerdo en las firmas de `ValidateCredentials` y `AppendMensaje` (no necesitan estar implementadas, solo la firma). Barbie empieza `http_client.py` y `udp_client.py`, que no dependen de nadie.
2. **Día 2–4:** cada uno implementa su módulo en paralelo contra el contrato del enunciado.
3. **Día 4–5:** integración — probar Cliente Benja / Cliente Seba en paralelo, prueba de timeout, escritura de los tres CSV.
4. **Día 5–6:** grabar el video, terminar el README (protocolo documentado + roles USM), pulir comentarios en el código.

## 5. Reglas de oro para evitar fricciones

- Nadie abre/escribe un CSV directamente salvo a través de las funciones de `storage` (Benja).
- Nadie del cliente (Barbie) modifica código del servidor (Benja/Seba) y viceversa — si algo del protocolo no cuadra, se avisa por chat y se ajusta el módulo correspondiente, no se "parchea" desde el otro lado.
- Cualquier cambio a los formatos de mensaje definidos en el enunciado se avisa a los tres antes de implementarlo.
