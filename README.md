# Laboratorio 1 — Redes de Computadores — Grupo 14

## Integrantes
| Nombre completo | Rol USM |
| --- | --- |
| Benjamín Torres | 202373539-6 |
| Sebastián Santander | 202373608-2 |
| Bárbara Camilo | 202304567-5 |

## Distribución de lenguajes (Grupo 14, número par)
- Servidor: **Go 1.20+** (`server-go/`)
- Cliente: **Python 3.10+** (`client-py/`)

## Compilación y ejecución

### Servidor (Go)
```bash
cd server-go
go run ./cmd/server
```
Puertos por defecto: HTTP `:8080`, TCP `:9000`, UDP `:9001`.

### Cliente (Python)
```bash
cd client-py
python3 main.py
```

## Protocolo — documentación formal

### HTTP
| Endpoint | Método | Body | Respuestas |
| --- | --- | --- | --- |
| `/register` | POST | `{"username","password"}` | 201 Created / 409 Conflict / 400 Bad Request |
| `/history` | GET | — | 200 OK + historial |

### TCP (delimitador `\n`)
| Comando | Formato | Respuesta éxito | Respuesta error |
| --- | --- | --- | --- |
| LOGIN | `LOGIN <user> <pass>` | `OK <token> <puerto_udp>` | `ERROR INVALID CREDENTIALS` |
| MSG | `MSG <token> <mensaje>` | `ACK` + broadcast `INCOMING <user> <mensaje>` a otros clientes | `ERROR SESSION EXPIRED` / `ERROR INVALID TOKEN` |

### UDP
| Comando | Formato | Efecto |
| --- | --- | --- |
| HEARTBEAT | `HEARTBEAT <token>` | Actualiza `timestamp_ultimo_heartbeat` en `sesiones.csv` |

Reglas de expiración: 30s sin primer latido, 60s sin heartbeat, 10min TTL absoluto de token.

## Arquitectura

El servidor mantiene tres servicios de red corriendo en paralelo, todos
sobre el mismo estado de sesiones en memoria (`session.Manager`):

- **HTTP** (`net/http`): registro de usuarios e historial de mensajes.
  Solo depende de los CSV de usuarios e historial, es independiente del
  resto.
- **TCP**: login y mensajería. Cada conexión corre en su propia goroutine,
  lo que permite atender múltiples clientes en simultáneo; la lectura usa
  `bufio.Reader.ReadString('\n')` porque TCP es un flujo de bytes, no de
  mensajes.
- **UDP**: recepción de heartbeats. No maneja conexiones — un único socket
  atiende los datagramas de todos los clientes — y corre en paralelo un
  *watchdog* que expira las sesiones que llevan demasiado tiempo sin latir.

El estado compartido (sesiones activas) vive protegido por un mutex en
`session.Manager`, consumido tanto por el servidor TCP como por el UDP.
La persistencia de cada CSV vive en su propio tipo con su propio mutex
(`UsuariosStore`, `HistorialStore`, `CSVSesiones`), para que nunca compitan
dos bloqueos sobre el mismo archivo.

Del lado del cliente, `tcp_client.py` implementa el mismo manejo de buffer
por línea que el servidor (a mano, ya que Python no trae un equivalente a
`bufio` para sockets crudos) y separa la recepción de broadcasts en un
hilo aparte para no bloquear la consola.

## Estructura de carpetas
```
server-go/
  cmd/server/main.go        # arma y levanta los tres servicios (integración)
  internal/storage/         # persistencia de usuarios.csv e historial.csv
  internal/httpserver/      # servicio HTTP: /register y /history
  internal/session/         # estado de sesiones compartido por TCP y UDP
  internal/tcpserver/       # servicio TCP: LOGIN / MSG / broadcast
  internal/udpserver/       # servicio UDP: heartbeat + watchdog
client-py/
  http_client.py            # POST /register y GET /history sobre socket TCP crudo
  tcp_client.py             # login, envío de mensajes e hilo receptor
  udp_client.py             # hilo de heartbeat
  main.py                   # orquesta todo lo anterior + consola no bloqueante
  probar_token_vencido.py   # herramienta para validar el Punto 8 de los "Requisitos Mínimos"
```

## Video de demostración
(https://usmcl-my.sharepoint.com/:v:/g/personal/btorres_usm_cl/IQBUGpKIm1vBR7CrOOliOGkTAUWn3adAsiH1aUhHH7ATS_I?e=eRx0Cb&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)
