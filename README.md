# Laboratorio 1 — Redes de Computadores — Grupo 14

## Integrantes
| Nombre completo | Rol USM |
| --- | --- |
| Benjamín Torres | 202373539-6 |
| Sebastián Santander | ... |
| Bárbara Camilo | ... |

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

## Estructura de carpetas
```
server-go/
  cmd/server/main.go        # integración final (todos)
  internal/storage/         # Benja: CSVStore con mutex
  internal/httpserver/      # Benja: /register /history
  internal/session/         # Seba: estado compartido TCP+UDP
  internal/tcpserver/       # Seba: LOGIN / MSG / broadcast
  internal/udpserver/       # Seba: heartbeat + watchdog
client-py/
  http_client.py            # Barbie: POST /register sobre socket TCP crudo
  tcp_client.py              # Barbie: login + envío + hilo receptor
  udp_client.py              # Barbie: hilo heartbeat
  main.py                    # Barbie: orquesta todo + consola no bloqueante
```

## Video de demostración
(enlace o archivo aquí)
