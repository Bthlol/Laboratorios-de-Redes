"""
Cliente integrado -- Componente 4, propiedad de Barbie.

Flujo:
  1. (Opcional) registrar usuario vía HTTP.
  2. Login vía TCP -> obtiene token + puerto UDP.
  3. Lanza hilo de heartbeat UDP y hilo receptor TCP.
  4. Loop principal en consola: leer input del usuario y enviar MSG,
     sin bloquear la recepción de mensajes entrantes (eso ya corre en
     su propio hilo gracias a tcp_client.start_receiver()).
"""
import sys

from http_client import register
from tcp_client import TCPClient
from udp_client import HeartbeatSender

SERVER_HOST = "127.0.0.1"
HTTP_PORT = 8080
TCP_PORT = 9000


def main():
    username = input("Usuario: ").strip()
    password = input("Password: ").strip()

    # 1. Registro (opcional si el usuario ya existe)
    status = register(SERVER_HOST, HTTP_PORT, username, password)
    print(f"Registro -> status {status}")

    # 2. Login TCP
    client = TCPClient(SERVER_HOST, TCP_PORT)
    client.connect()
    if not client.login(username, password):
        sys.exit(1)

    # 3. Hilos en segundo plano
    heartbeat = HeartbeatSender(SERVER_HOST, client.udp_port, client.token)
    heartbeat.start()
    client.start_receiver()

    print("Conectado. Escribe mensajes y presiona Enter para enviarlos ('/salir' para terminar).")

    # 4. Loop principal de consola (no bloquea recepción, corre en el hilo main)
    try:
        while True:
            texto = input()
            if texto.strip() == "/salir":
                break
            client.send_message(texto)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        heartbeat.stop()
        client.stop()


if __name__ == "__main__":
    main()
