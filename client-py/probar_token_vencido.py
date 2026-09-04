"""
Script auxiliar SOLO para el paso 8 de la demo (prueba de sesión expirada).

No reemplaza a main.py -- es una herramienta chica para mostrar en cámara
que el servidor rechaza un token ya revocado cuando se presenta en una
conexión TCP NUEVA (la conexión original del cliente revocado ya la cerró
el servidor solo en el paso 7, por eso no sirve reusarla).

Uso:
    python3 probar_token_vencido.py <token>

El <token> es el que imprimió el Cliente B (generado por la segunda terminal 
abierta inicialmente) al hacer LOGIN al principio de la demo (se debe obtener 
de allí).
"""
import socket
import sys

SERVER_HOST = "127.0.0.1"
TCP_PORT = 9000


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 probar_token_vencido.py <token>")
        sys.exit(1)

    token = sys.argv[1]
    print(f"Abriendo una conexión TCP NUEVA hacia {SERVER_HOST}:{TCP_PORT}...")
    with socket.create_connection((SERVER_HOST, TCP_PORT), timeout=3) as s:
        mensaje = f"MSG {token} intento tras revocacion\n"
        print(f"Enviando: {mensaje.strip()!r}")
        s.sendall(mensaje.encode("utf-8"))
        respuesta = s.recv(1024).decode(errors="replace").strip()
        print(f"Respuesta del servidor: {respuesta!r}")

        if respuesta == "ERROR SESSION EXPIRED":
            print("\n✅ Confirmado: el servidor rechazó el token vencido correctamente.")
        else:
            print("\n⚠️  Respuesta inesperada, revisar.")


if __name__ == "__main__":
    main()
