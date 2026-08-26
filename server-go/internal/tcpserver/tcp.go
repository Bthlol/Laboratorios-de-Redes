// Paquete tcpserver: propiedad de Persona B.
//
// Componente 2: LOGIN, MSG/broadcast. Cada conexión corre en su propia
// goroutine (concurrencia nativa de Go). Usa session.Manager para el
// estado compartido y storage.CSVStore (de Persona A) para persistir.
package tcpserver

import (
	"bufio"
	"net"
	"strings"

	"lab1-grupo14/server/internal/session"
)

type Server struct {
	Addr     string
	Sessions *session.Manager
}

func (s *Server) ListenAndServe() error {
	ln, err := net.Listen("tcp", s.Addr)
	if err != nil {
		return err
	}
	defer ln.Close()
	for {
		conn, err := ln.Accept()
		if err != nil {
			continue
		}
		go s.handleConn(conn)
	}
}

func (s *Server) handleConn(conn net.Conn) {
	defer conn.Close()
	reader := bufio.NewReader(conn)
	for {
		line, err := reader.ReadString('\n') // delimitador \n según el enunciado
		if err != nil {
			return // TODO(B): si el socket pertenece a una sesión activa, invalidarla (LOGOUT implícito)
		}
		line = strings.TrimSpace(line)
		fields := strings.SplitN(line, " ", 3)
		if len(fields) == 0 {
			continue
		}
		switch fields[0] {
		case "LOGIN":
			// TODO(B): fields[1]=username, fields[2]=password
			//   validar contra storage de Persona A
			//   OK -> s.Sessions.Crear(...) y asignar/levantar el servidor UDP para esa sesión
			//   responder "OK <token> <puerto_udp>\n" o "ERROR INVALID CREDENTIALS\n"
		case "MSG":
			// TODO(B): fields[1]=token, fields[2]=contenido
			//   s.Sessions.Validar(token) -> si falla: "ERROR SESSION EXPIRED\n" / "ERROR INVALID TOKEN\n"
			//   si ok: guardar en historial.csv, responder "ACK\n", Sessions.Broadcast(...)
		default:
			// comando desconocido
		}
	}
}
